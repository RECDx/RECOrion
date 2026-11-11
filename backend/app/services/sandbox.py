"""
Kod Çalıştırma Ortamı (ADIM 16.2): AI personelin yazdığı kodun RECOrion içinde denenmesi.

- Projenin Gitea deposundan istenen dalın arşivi alınır, iç ağdaki sandbox servisine gönderilir. Servis her koşu için yeni,
  sınırlı, root olmayan bir kap açar; bağımlılıkları kurar, ağı keser, testleri (pytest / npm test / scripts/recorion_test.sh)
  çalıştırır, kabı siler. Kod ne RECOrion veritabanına ne gizli bilgilere erişir.
- Koşu `test_runs` tablosuna yazılır; proje geçmişine TEST_RUN olayı düşer. Work Area'da projenin "Testler" sekmesinde ve
  Test Uzmanı'nın adım çıktısında görünür.
- AI Test Uzmanı (unvanında "test", "QA" veya "kalite güvence" geçen AI personel) deposu olan projede çıktısını ürettiğinde
  koşu kendiliğinden yapılır; AI gerçek sonuçları okuyup test raporunu bu sonuçlara göre tamamlar (agent_work).
"""
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Project, Task, TestRun
from app.services import code_repo, task_flow

logger = logging.getLogger("recorion.sandbox")

RUN_TIMEOUT = 900  # kurulum + test üst süresi (servis kendi içinde aşama başına 300 sn sınırlar)
MAX_ARCHIVE = 25 * 1024 * 1024
TEST_ROLE = re.compile(r"test|\bqa\b|kalite güvence", re.I)
STATUS_TR = {"RUNNING": "Çalışıyor", "PASSED": "Geçti", "FAILED": "Kaldı", "NO_TESTS": "Test bulunamadı", "ERROR": "Çalıştırılamadı"}


class SandboxError(Exception):
    pass


def enabled() -> bool:
    return bool(settings.SANDBOX_URL) and code_repo.enabled()


def is_test_role(role: Optional[str]) -> bool:
    return bool(role and TEST_ROLE.search(role))


def now() -> datetime:
    return datetime.now(timezone.utc)


async def _archive(project: Project, ref: str) -> bytes:
    base = settings.GITEA_URL.rstrip("/") + "/api/v1"
    try:
        async with httpx.AsyncClient(timeout=60, headers={"Authorization": f"token {settings.GITEA_TOKEN}"}) as c:
            r = await c.get(f"{base}/repos/{project.repo_owner}/{project.repo_name}/archive/{ref}.zip")
    except httpx.HTTPError as exc:
        raise SandboxError(f"Kod deposuna ulaşılamadı ({exc.__class__.__name__}).")
    if r.status_code == 404:
        raise SandboxError(f"'{ref}' dalı depoda bulunamadı.")
    if r.status_code != 200:
        raise SandboxError(f"Depo arşivi alınamadı ({r.status_code}).")
    if len(r.content) > MAX_ARCHIVE:
        raise SandboxError("Depo çalıştırma ortamı için çok büyük (25 MB üstü).")
    return r.content


async def _sha(project: Project, ref: str) -> Optional[str]:
    try:
        data = await code_repo._exists(f"/repos/{project.repo_owner}/{project.repo_name}/branches/{ref}")
        return ((data or {}).get("commit") or {}).get("id")
    except code_repo.RepoError:
        return None


async def execute(archive: bytes) -> Dict[str, Any]:
    """Arşivi sandbox servisine gönderir, sonucu döner (testlerde taklit edilir)."""
    try:
        async with httpx.AsyncClient(timeout=RUN_TIMEOUT) as c:
            r = await c.post(settings.SANDBOX_URL.rstrip("/") + "/run", content=archive, headers={"Content-Type": "application/zip"})
    except httpx.HTTPError as exc:
        raise SandboxError(f"Kod çalıştırma ortamına ulaşılamadı ({exc.__class__.__name__}).")
    if r.status_code != 200:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = r.text[:200]
        raise SandboxError(f"Kod çalıştırma ortamı hata verdi ({r.status_code}): {detail}")
    return r.json()


def _totals(result: Dict[str, Any]) -> Dict[str, int]:
    t = {"passed": 0, "failed": 0, "skipped": 0}
    for p in result.get("projects") or []:
        test = p.get("test") or {}
        t["passed"] += int(test.get("passed") or 0)
        t["failed"] += int(test.get("failed") or 0) + int(test.get("errors") or 0)
        t["skipped"] += int(test.get("skipped") or 0)
    smoke = result.get("smoke") or {}
    for c in smoke.get("checks") or []:  # duman testi denetimleri de sayılır (#734)
        key = "passed" if c.get("ok") is True else "failed" if c.get("ok") is False else "skipped"
        t[key] += 1
    t["failed"] += sum(1 for s in smoke.get("services") or [] if not s.get("ready"))
    return t


SMOKE_TR = {"PASSED": "Geçti", "FAILED": "Kaldı", "NO_SMOKE": "Yapılmadı (recorion.json yok)", "ERROR": "Çalıştırılamadı"}


def smoke_status(run: Optional[TestRun]) -> Optional[str]:
    return ((run.result or {}).get("smoke") or {}).get("status") if run else None


def smoke_md(smoke: Dict[str, Any]) -> List[str]:
    """Duman testi bölümü: uygulama açıldı mı, denetimler, README."""
    if not smoke:
        return []
    lines = ["", f"### Duman testi (uygulamayı açıp deneme) — {SMOKE_TR.get(smoke.get('status'), smoke.get('status'))}"]
    if smoke.get("note"):
        lines.append(f"- Not: {smoke['note']}")
    for s in smoke.get("services") or []:
        state = f"açıldı (HTTP {s.get('ready_status')})" if s.get("ready") else f"AÇILMADI — {s.get('error') or 'yanıt yok'}"
        lines.append(f"- Hizmet `{s.get('name')}` (`{s.get('dir')}`, port {s.get('port')}): {state}")
        if not s.get("ready") and s.get("log"):
            lines += ["```text", s["log"][-1500:], "```"]
    for c in smoke.get("checks") or []:
        mark = "✓" if c.get("ok") is True else "✗" if c.get("ok") is False else "–"
        lines.append(f"- {mark} {c.get('name')} ({'arayüz' if c.get('type') == 'browser' else 'API'}): {(c.get('detail') or '')[:300]}")
    rd = smoke.get("readme") or {}
    if rd:
        lines.append(f"- README: {'var, ' + str(rd.get('chars')) + ' karakter' if rd.get('file') else 'YOK'}"
                     + ("" if rd.get("ok") else " — kurulum talimatı eksik/yetersiz"))
    return lines


async def start(db: AsyncSession, project: Project, ref: str, actor_id=None, task: Optional[Task] = None) -> TestRun:
    run = TestRun(tenant_id=project.tenant_id, project_id=project.id, task_id=task.id if task else None, ref=ref,
                  status="RUNNING", started_by_actor_id=actor_id, created_at=now())
    db.add(run)
    await db.flush()
    return run


async def finish(db: AsyncSession, project: Project, run: TestRun, task: Optional[Task] = None) -> TestRun:
    """Koşuyu yapar ve sonucu kaydeder. Hata akışı durdurmaz: koşu ERROR olarak kaydedilir."""
    try:
        if not code_repo.active(project):
            raise SandboxError("Bu projenin kod deposu açık değil.")
        run.commit_sha = await _sha(project, run.ref)
        result = await execute(await _archive(project, run.ref))
        run.result, run.status = result, result.get("status") if result.get("status") in STATUS_TR else "ERROR"
        t = _totals(result)
        run.passed, run.failed, run.skipped = t["passed"], t["failed"], t["skipped"]
    except SandboxError as exc:
        run.status, run.error = "ERROR", str(exc)
    except Exception as exc:  # beklenmeyen: koşu kaydı açık kalmasın
        logger.exception("Test koşusu başarısız")
        run.status, run.error = "ERROR", f"Beklenmeyen hata: {exc.__class__.__name__}"
    run.finished_at = now()
    note = f"{run.ref}: {STATUS_TR.get(run.status, run.status)} · {run.passed} geçti, {run.failed} kaldı" + (f" · {run.error}" if run.error else "")
    await task_flow.log(db, project, task, "TEST_RUN", run.started_by_actor_id, note,
                        {"test_run_id": str(run.id), "status": run.status, "passed": run.passed, "failed": run.failed})
    if task is not None and run.status in ("PASSED", "FAILED", "ERROR"):
        # İSTEK #742: gerçek test sonucu doğrulanabilir sinyaldir (yazılıma özgü); ortam hatası AI'ın hatası sayılmaz
        from app.services import learning_records
        ok = run.status == "PASSED"
        await db.flush()
        await learning_records.capture_task(
            task, project, "TEST_RUN", "DOGRU" if ok else "YANLIS", feedback=report_md(run)[:4000],
            cause=None if ok else learning_records.test_cause(run.status, run.error), cause_by=None if ok else "SYSTEM",
            data={"test_run_id": str(run.id), "status": run.status, "passed": run.passed, "failed": run.failed},
            lesson=not ok and run.status == "FAILED")
    return run


def report_md(run: TestRun) -> str:
    """Koşunun sistem tarafından yazılan (AI'ın değiştiremediği) özeti: adım çıktısına eklenir."""
    lines = ["## Gerçek test koşusu (RECOrion Kod Çalıştırma Ortamı)", "",
             f"- Dal: `{run.ref}`" + (f" · commit `{run.commit_sha[:10]}`" if run.commit_sha else ""),
             f"- Sonuç: **{STATUS_TR.get(run.status, run.status)}** · {run.passed} geçti · {run.failed} kaldı · {run.skipped} atlandı"]
    if run.error:
        lines.append(f"- Hata: {run.error}")
    res = run.result or {}
    if res.get("note"):
        lines.append(f"- Not: {res['note']}")
    for p in res.get("projects") or []:
        test, inst = p.get("test") or {}, p.get("install") or {}
        lines.append(f"\n### `{p.get('dir')}` ({p.get('kind')}) — {STATUS_TR.get(test.get('status'), test.get('status') or '-')}")
        if inst and not inst.get("ok"):
            lines += ["Bağımlılık kurulumu başarısız:", "```text", (inst.get("log") or "")[-1500:], "```"]
        for f in (test.get("failures") or [])[:10]:
            lines.append(f"- ✗ `{f.get('name')}`: {(f.get('message') or '').strip()[:300]}")
        if test.get("status") in ("FAILED", "TIMEOUT") and not test.get("failures"):
            lines += ["```text", (test.get("log") or "")[-2000:], "```"]
    lines += smoke_md(res.get("smoke") or {})
    return "\n".join(lines)


ACCEPT_ROLE = re.compile(r"kabul|teslim|duman|kurulum|yayın|canlıya", re.I)


def is_acceptance_step(task: Task) -> bool:
    return bool(ACCEPT_ROLE.search(task.title or ""))


async def acceptance_gate(db: AsyncSession, project: Project, task: Task) -> Optional[str]:
    """Kabul kapısı (#734): deposu olan projede kabul/teslim adımı ya da projenin son açık adımı onaylanırken uygulamanın
    gerçekten açılıp denendiği (testler + duman testi geçti) aranır. Sorun varsa onaylayıcıya gösterilecek metin döner."""
    from sqlalchemy import select

    if not enabled() or not code_repo.active(project):
        return None
    tasks = (await db.execute(select(Task).where(Task.project_id == project.id))).scalars().all()
    last_open = not any(t.id != task.id and t.status not in task_flow.CLOSED for t in tasks)
    if not (is_acceptance_step(task) or last_open):
        return None
    refs = [r for r in (task.repo_branch, code_repo.BASE_BRANCH) if r]
    run = (await db.execute(select(TestRun).where(TestRun.project_id == project.id, TestRun.ref.in_(refs), TestRun.status != "RUNNING")
                            .order_by(TestRun.created_at.desc()).limit(1))).scalar_one_or_none()
    if not run:
        return ("Bu proje için uygulama hiç çalıştırılıp denenmedi (Kod Çalıştırma Ortamı'nda koşu yok). Kabul etmeden önce "
                "Testler sekmesinden testleri ve duman testini çalıştırın.")
    smoke = smoke_status(run)
    problems = []
    if run.status != "PASSED":
        problems.append(f"son koşu {STATUS_TR.get(run.status, run.status)} ({run.passed} geçti, {run.failed} kaldı)")
    if smoke != "PASSED":
        problems.append("duman testi " + (SMOKE_TR.get(smoke, smoke) if smoke else "yapılmadı").lower()
                        + " — uygulamanın talimatla açılıp temel akışın çalıştığı doğrulanmadı")
    readme = (((run.result or {}).get("smoke") or {}).get("readme") or {})
    if readme and not readme.get("ok"):
        problems.append("README (kurulum talimatı) eksik veya yetersiz")
    sha = await _sha(project, run.ref)
    if sha and run.commit_sha and sha != run.commit_sha:
        problems.append(f"son koşudan sonra '{run.ref}' dalı değişti; sonuç güncel değil")
    if not problems:
        return None
    return "Kabul öncesi denetim: " + "; ".join(problems) + "."


MAX_FIX_ROUNDS = 2
FIX_PREFIX = re.compile(r"^(Test düzeltmesi|Yeniden test) \d+: ")
PATH_HINT = re.compile(r"[\w./-]+\.(?:py|js|jsx|ts|tsx|mjs|cjs|html|css|sql|json|toml|txt|cfg|ini|yml|yaml|sh)\b")


def _base_title(title: str) -> str:
    while FIX_PREFIX.match(title or ""):
        title = FIX_PREFIX.sub("", title, count=1)
    return title


def root_of(task: Task):
    """Düzeltme/yeniden test adımının kök test adımı (kendisi kökse kendi kimliği)."""
    return task.fix_of_task_id or task.id


def _report_text(run: TestRun) -> str:
    """Kalan test adları, mesajları ve kayıt sonları + duman testi ayrıntısı: geliştirici eşleştirmesi için."""
    parts = [report_md(run)]
    for p in (run.result or {}).get("projects") or []:
        parts.append((p.get("test") or {}).get("log") or "")
        parts.append(f"dir:{p.get('dir')} kind:{p.get('kind')}")
    for s in ((run.result or {}).get("smoke") or {}).get("services") or []:
        parts.append(f"{s.get('dir')} {s.get('log') or ''} {s.get('error') or ''}")
    return "\n".join(parts)


def _score(files, text: str) -> int:
    """Geliştiricinin yazdığı dosyaların hata metninde geçme puanı (tam yol 3, dosya adı 2, dosya kökü ≥4 harf 1)."""
    score = 0
    low = text.lower()
    for path in files:
        if path.startswith("docs/") or path.startswith("tests/") or "/tests/" in path or path.rsplit("/", 1)[-1].startswith("test_"):
            continue
        p, name = path.lower(), path.rsplit("/", 1)[-1].lower()
        stem = name.rsplit(".", 1)[0]
        if p in low:
            score += 3
        elif name in low:
            score += 2
        elif len(stem) >= 4 and re.search(rf"\b{re.escape(stem)}\b", low):
            score += 1
    return score


async def pick_developer(db: AsyncSession, project: Project, test_task: Task, run: TestRun, tasks) -> Optional[tuple]:
    """F99: kalan testlerle ilgili kodu yazan AI geliştiriciyi bulur. Her geliştirici adımının son çıktısındaki dosyalar hata
    metninde (test adı, mesaj, iz, duman testi kaydı) aranır; en çok eşleşen seçilir. Eşleşme yoksa: kalan Python testleri için
    .py yazan, Node testleri için .js yazan, o da yoksa test adımından önceki son geliştirici."""
    from app.db.models import Actor
    from app.services.agent_work import artifact_text, latest_artifact

    text = _report_text(run)
    order = test_task.order_index or 0
    root = root_of(test_task)
    cands = []
    for t in tasks:
        if t.id == test_task.id or t.fix_kind or (t.order_index or 0) > order or not t.assignee_actor_id or not t.repo_branch:
            continue
        if t.status == "CANCELLED" or t.id == root:
            continue
        a = await db.get(Actor, t.assignee_actor_id)
        if not a or a.actor_type != "AI_AGENT" or is_test_role(a.role) or is_acceptance_step(t):
            continue
        files = list(code_repo.files_from_output(t, await artifact_text(await latest_artifact(db, t.id), 200_000) or ""))
        cands.append((t, a, files))
    if not cands:
        return None
    scored = [(_score(files, text), i, t, a, files) for i, (t, a, files) in enumerate(cands)]
    best = max(scored, key=lambda x: (x[0], x[1]))
    if best[0] > 0:
        return best[2], best[3], "hata metninde yazdığı dosyalar geçiyor"
    kinds = {(p.get("kind")) for p in (run.result or {}).get("projects") or []
             if (p.get("test") or {}).get("status") in ("FAILED", "TIMEOUT", "INSTALL_FAILED")}
    for kind, exts in (("python", (".py",)), ("node", (".js", ".mjs", ".ts", ".jsx", ".tsx"))):
        if kind in kinds:
            match = [c for c in scored if any(f.endswith(exts) and not f.startswith("docs/") for f in c[4])]
            if match:
                c = match[-1]
                return c[2], c[3], f"kalan {kind} testleri; bu dilde kod yazan geliştirici"
    c = scored[-1]
    return c[2], c[3], "test adımından önceki son geliştirici"


async def latest_lineage_run(db: AsyncSession, task: Task) -> Optional[TestRun]:
    """Kök test adımı ve yeniden testlerinin en son biten koşusu (F109: düzeltme adımı güncel raporla çalışır)."""
    from sqlalchemy import or_, select

    root = root_of(task)
    ids = (await db.execute(select(Task.id).where(or_(Task.id == root, Task.fix_of_task_id == root)))).scalars().all()
    return (await db.execute(select(TestRun).where(TestRun.task_id.in_(ids), TestRun.status != "RUNNING")
                             .order_by(TestRun.created_at.desc()).limit(1))).scalar_one_or_none()


async def _close_lineage(db: AsyncSession, project: Project, test_task: Task, tasks) -> list:
    """F105: testler geçti → aynı test adımının açık düzeltme/yeniden test adımları kapanır."""
    root, closed = root_of(test_task), []
    for t in tasks:
        if t.id != test_task.id and t.fix_of_task_id == root and t.status not in task_flow.CLOSED:
            try:
                await task_flow.request_cancel(db, t, project, None, f"Testler geçti ({test_task.title}); bu tur artık gerekmiyor.")
                closed.append(t.title)
            except Exception:  # akış sinyali gitmezse yönetici elle iptal eder
                logger.warning("Gereksiz düzeltme turu kapatılamadı (%s)", t.id, exc_info=True)
    if closed:
        await task_flow.log(db, project, test_task, "TEST_FIX_CLOSED", None, "Testler geçti; kapatılan turlar: " + ", ".join(closed))
    return closed


async def schedule_fix_loop(db: AsyncSession, project: Project, test_task: Task, run: TestRun) -> Optional[str]:
    """Test/kabul koşusundan sonra düzeltme döngüsü (Aşama 2 bulgularıyla yeniden: F99, F100, F103, F105, F109).

    - Geçti: aynı test adımının açık turları kapanır.
    - Kaldı ve açık tur varsa yeni tur açılmaz; başlamamış düzeltme adımı güncel raporla güncellenir (başlamışsa adım
      çalışırken zaten en güncel koşuyu okur).
    - Kaldı ve açık tur yoksa: kalan testlerle ilgili kodu yazan geliştiriciye "Test düzeltmesi N" HEMEN başlar (test adımının
      onayını beklemez: kilitlenme F103), ardından test adımı ve düzeltme bitince "Yeniden test N" çalışır. En fazla
      MAX_FIX_ROUNDS tur; sonrası proje yöneticisine kalır. Dönen metin adım çıktısına eklenir."""
    from sqlalchemy import func, select

    tasks = (await db.execute(select(Task).where(Task.project_id == project.id).order_by(Task.order_index))).scalars().all()
    root = root_of(test_task)
    lineage = [t for t in tasks if t.fix_of_task_id == root]
    if run.status == "PASSED":
        closed = await _close_lineage(db, project, test_task, tasks)
        return f"_Sistem: testler geçti; gereksiz kalan düzeltme turları kapatıldı: {', '.join(closed)}._" if closed else None
    if run.status != "FAILED":
        return None
    failures = report_md(run)[:3500]
    open_fix = next((t for t in lineage if t.fix_kind == "FIX" and t.status not in task_flow.CLOSED), None)
    if open_fix:
        if open_fix.status in ("BACKLOG", "READY"):
            open_fix.description = _fix_description(test_task, failures)
        await task_flow.log(db, project, test_task, "TEST_FIX_UPDATED", None,
                            f"Açık tur sürüyor: '{open_fix.title}' en güncel koşu sonucuyla çalışacak; yeni tur açılmadı.")
        return f"_Sistem: açık düzeltme turu (**{open_fix.title}**) sürüyor; yeni tur açılmadı, düzeltme en güncel koşu sonucuyla yapılacak._"
    rounds = sum(1 for t in lineage if t.fix_kind == "FIX" and t.status != "CANCELLED")
    if rounds >= MAX_FIX_ROUNDS:
        await task_flow.log(db, project, test_task, "TEST_FIX_LIMIT", None, f"{MAX_FIX_ROUNDS} düzeltme turundan sonra testler hâlâ kalıyor.")
        return (f"_Sistem: {MAX_FIX_ROUNDS} düzeltme turundan sonra testler hâlâ kalıyor; yeni düzeltme adımı açılmadı. "
                "Karar proje yöneticisinde._")
    dev = await pick_developer(db, project, test_task, run, tasks)
    if not dev:
        await task_flow.log(db, project, test_task, "TEST_FIX_SKIPPED", None, "Kodu yazan AI personel adımı bulunamadı.")
        return "_Sistem: kodu yazan AI personel adımı bulunamadığı için düzeltme adımı açılamadı; karar proje yöneticisinde._"
    dev_task, dev_agent, why = dev
    root_task = next((t for t in tasks if t.id == root), test_task)
    n = rounds + 1
    last = (await db.execute(select(func.coalesce(func.max(Task.order_index), 0)).where(Task.project_id == project.id))).scalar()
    fix = Task(project_id=project.id, title=f"Test düzeltmesi {n}: {_base_title(dev_task.title)}"[:255], status="BACKLOG",
               description=_fix_description(test_task, failures),
               acceptance_criteria="Kalan testler geçecek şekilde uygulama kodu düzeltildi; değişiklik ve gerekçe yazıldı.",
               assignee_actor_id=dev_agent.id, depends_on=[], order_index=last + 1, fix_of_task_id=root, fix_kind="FIX",
               department_id=dev_task.department_id, job_title_id=dev_task.job_title_id, reviewer_actor_id=None,
               approver_actor_id=dev_task.approver_actor_id, requires_approval=dev_task.requires_approval, estimated_effort=1)
    db.add(fix)
    await db.flush()
    retest = Task(project_id=project.id, title=f"Yeniden test {n}: {_base_title(root_task.title)}"[:255], status="BACKLOG",
                  description=(f"'{fix.title}' adımındaki düzeltmeden sonra testleri yeniden çalıştır. Önceki turda kalan testler:\n\n{failures}\n\n"
                               "Testler depoda duruyor; gerekirse güncelle ya da yeni test ekle."),
                  acceptance_criteria="Testler Kod Çalıştırma Ortamı'nda yeniden çalıştırıldı ve sonuç değerlendirildi.",
                  assignee_actor_id=root_task.assignee_actor_id, depends_on=[str(fix.id), str(test_task.id)], order_index=last + 2,
                  fix_of_task_id=root, fix_kind="RETEST", department_id=root_task.department_id, job_title_id=root_task.job_title_id,
                  reviewer_actor_id=None, approver_actor_id=root_task.approver_actor_id, requires_approval=root_task.requires_approval,
                  estimated_effort=1)
    db.add(retest)
    await db.flush()
    await task_flow.log(db, project, test_task, "TEST_FIX_LOOP", None,
                        f"Tur {n}: '{fix.title}' → {dev_agent.display_name} ({why}); ardından '{retest.title}'.",
                        {"fix_task_id": str(fix.id), "retest_task_id": str(retest.id), "round": n, "why": why})
    if project.manager_actor_id:
        try:
            await task_flow.notify(db, project.manager_actor_id,
                                   f"{project.name}: testler kaldı ({run.passed} geçti, {run.failed} kaldı). '{fix.title}' "
                                   f"{dev_agent.display_name}'e açıldı ve hemen başlıyor; ardından testler yeniden çalışacak.")
        except Exception:  # bildirim akışı durdurmaz
            logger.warning("Düzeltme döngüsü bildirimi gönderilemedi", exc_info=True)
    return (f"_Sistem: kalan testler için **{fix.title}** adımı {dev_agent.display_name}'e açıldı ({why}) ve hemen başlıyor; "
            f"ardından **{retest.title}** çalışacak (en fazla {MAX_FIX_ROUNDS} tur)._")


def _fix_description(test_task: Task, failures: str) -> str:
    return (f"'{test_task.title}' adımında RECOrion Kod Çalıştırma Ortamı'nda çalışan testler kaldı. Kalan testleri inceleyip "
            "UYGULAMA kodunu düzelt (testi atlatmak için testi değiştirme). Test gerçekten yanlış beklenti kuruyorsa bunu "
            "gerekçesiyle yaz; test dosyasını yalnız o durumda düzelt. Yalnız gereken dosyaları depodaki yollarıyla ver.\n\n"
            f"{failures}")


async def wake_project(project: Project) -> None:
    """Yeni açılan/iptal edilen adımları proje akışı hemen görsün."""
    from app.workflows import engine
    try:
        await engine.signal_project(str(project.id), "refresh")
    except Exception:
        logger.info("Proje akışı yenilenemedi (%s)", project.id)


def view(run: TestRun) -> Dict[str, Any]:
    return {"id": str(run.id), "task_id": str(run.task_id) if run.task_id else None, "ref": run.ref, "commit_sha": run.commit_sha,
            "status": run.status, "status_label": STATUS_TR.get(run.status, run.status), "passed": run.passed, "failed": run.failed,
            "skipped": run.skipped, "error": run.error, "result": run.result, "started_by_actor_id": str(run.started_by_actor_id) if run.started_by_actor_id else None,
            "created_at": run.created_at, "finished_at": run.finished_at}
