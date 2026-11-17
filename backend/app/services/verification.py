"""
İSTEK #752: Teslimata göre doğrulama.

Planda her adım için iki şey yazılır: ne teslim edilecek (deliverable) ve tamam olduğu nasıl anlaşılacak (verification:
tür + yöntem). Sistem onaydan önce ikinci maddeyi kontrol eder; eksikse onay durur, eksikle onay ancak gerekçeyle verilir
ve kayda geçer. Proje için "N teslimattan M tanesi doğrulandı" kapsam raporu üretilir.

Türler:
  TEST       Otomatik test — kodlu projede sistem adımın dalını Kod Çalıştırma Ortamı'nda koşar (testler, duman testi,
             tıklama taraması); kodsuz projede kanıt gibi değerlendirilir.
  MEASURE    Ölçüm — sorumlu ölçülen değeri girer (ör. OEE %62, açılma oranı %31).
  EVIDENCE   Kanıt — sorumlu kanıt ekler (not, bağlantı, Proje Eki); AI adımında adımın çıktısı kanıttır.
  CHECKLIST  Kontrol listesi — maddelerin hepsi işaretlenir.
  HUMAN      İnsan onayı — belirlenen kişinin onayı doğrulamadır.
"""
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, AgentDocument, Artifact, Project, Task, TestRun

TYPES = ("TEST", "MEASURE", "EVIDENCE", "CHECKLIST", "HUMAN")
TYPE_TR = {"TEST": "Otomatik test", "MEASURE": "Ölçüm", "EVIDENCE": "Kanıt", "CHECKLIST": "Kontrol listesi", "HUMAN": "İnsan onayı"}
STATUS_TR = {"VERIFIED": "Doğrulandı", "MISSING": "Eksik", "WAIVED": "Gerekçeyle kabul", "PENDING": "Bekliyor"}
MAX_EVIDENCE, MAX_ITEMS = 20, 20


def now() -> datetime:
    return datetime.now(timezone.utc)


def clean_type(value: Any, human: bool = False) -> str:
    v = str(value or "").strip().upper().replace("İ", "I")
    if v in TYPES:
        return v
    return "HUMAN" if human else "EVIDENCE"


def checklist_items(method: str) -> List[str]:
    """Kontrol listesi maddeleri yöntem metninden çıkarılır (satır, ';' ya da madde işareti)."""
    parts = re.split(r"\n|;|•|(?:^|\s)-\s", method or "")
    return [p.strip(" .-\t") for p in parts if len(p.strip(" .-\t")) >= 3][:MAX_ITEMS]


def init_for_task(step: Dict[str, Any], human: bool) -> Optional[Dict[str, Any]]:
    """Plan adımından görevin doğrulama kaydı (plan onayında)."""
    method = str(step.get("verification") or "").strip()[:600]
    if not method and not step.get("deliverable"):
        return None
    vtype = clean_type(step.get("verification_type"), human)
    v = {"type": vtype, "method": method, "evidence": [], "measure": None, "status": "PENDING"}
    if vtype == "CHECKLIST":
        v["checklist"] = [{"item": i, "ok": False} for i in (checklist_items(method) or [method or "Teslimat kontrol edildi"])]
    return v


def _v(task: Task) -> Dict[str, Any]:
    return dict(task.verification or {})


async def _latest_run(db: AsyncSession, project: Project, task: Task) -> Optional[TestRun]:
    from app.services import code_repo

    refs = [r for r in (task.repo_branch, code_repo.BASE_BRANCH if task.status == "DONE" else None) if r]
    if not refs:
        return None
    return (await db.execute(select(TestRun).where(TestRun.project_id == project.id, TestRun.ref.in_(refs), TestRun.status != "RUNNING")
                             .order_by(TestRun.created_at.desc()).limit(1))).scalar_one_or_none()


async def _has_output(db: AsyncSession, task: Task) -> Optional[int]:
    return (await db.execute(select(Artifact.version).where(Artifact.task_id == task.id).order_by(Artifact.version.desc()).limit(1))).scalar()


async def _is_ai(db: AsyncSession, task: Task) -> bool:
    if not task.assignee_actor_id:
        return False
    a = await db.get(Actor, task.assignee_actor_id)
    return bool(a and a.actor_type == "AI_AGENT")


async def evaluate(db: AsyncSession, project: Project, task: Task) -> Tuple[str, str]:
    """(durum, açıklama) — durum VERIFIED | MISSING | WAIVED | PENDING (teslim edilmemiş, insan onayı bekleyen ya da eski plan).
    Henüz teslim edilmemiş adımın eksiği "Eksik" değil "Bekliyor" sayılır; eksik, onaya gelen ya da biten adım içindir."""
    st, why = await _evaluate(db, project, task)
    if st == "MISSING" and task.status not in ("WAITING_APPROVAL", "QUARANTINED", "DONE"):
        return "PENDING", f"Adım henüz teslim edilmedi · {why}"
    return st, why


async def _evaluate(db: AsyncSession, project: Project, task: Task) -> Tuple[str, str]:
    from app.services import code_repo, sandbox

    v = _v(task)
    if not v:
        return "PENDING", "Bu adım için doğrulama yöntemi tanımlanmamış (eski plan)."
    if v.get("waived"):
        return "WAIVED", f"Eksikle kabul edildi: {v['waived'].get('reason')}"
    if v.get("status") == "VERIFIED" and task.status == "DONE":
        return "VERIFIED", v.get("note") or "Onayla doğrulandı."
    t = v.get("type")
    evidence = v.get("evidence") or []
    if t == "TEST" and sandbox.enabled() and code_repo.active(project):
        run = await _latest_run(db, project, task)
        if not run:
            return "MISSING", "Adımın kodu henüz Kod Çalıştırma Ortamı'nda çalıştırılıp denenmedi."
        smoke = sandbox.smoke_status(run)
        probs = []
        if run.status != "PASSED":
            probs.append(f"son test koşusu {sandbox.STATUS_TR.get(run.status, run.status)} ({run.passed} geçti, {run.failed} kaldı)")
        if smoke not in ("PASSED", "NO_SMOKE"):
            probs.append("duman testi " + sandbox.SMOKE_TR.get(smoke, smoke or "yapılmadı").lower())
        loose = (run.result or {}).get("loosened") or []
        if loose:
            probs.append("önceden doğrulanmış denetimler gevşetildi: " + ", ".join(x["name"] for x in loose[:5]))
        if probs:
            return "MISSING", "; ".join(probs)
        return "VERIFIED", f"Test koşusu geçti ({run.passed} denetim) · {run.ref}"
    if t == "MEASURE":
        m = v.get("measure")
        return ("VERIFIED", f"Ölçüm: {m.get('value')} {m.get('unit') or ''}".strip()) if m and str(m.get("value") or "").strip() \
            else ("MISSING", "Ölçüm değeri girilmedi.")
    if t == "CHECKLIST":
        items = v.get("checklist") or []
        left = [i["item"] for i in items if not i.get("ok")]
        return ("MISSING", f"{len(left)}/{len(items)} madde işaretlenmedi: " + "; ".join(left[:4])) if left or not items \
            else ("VERIFIED", f"{len(items)} maddenin hepsi işaretlendi.")
    if t == "HUMAN":
        return "PENDING", "Doğrulama, belirlenen kişinin onayıyla yapılır."
    # EVIDENCE (ve kodsuz projede TEST)
    if evidence:
        return "VERIFIED", f"{len(evidence)} kanıt eklendi."
    if await _is_ai(db, task):
        ver = await _has_output(db, task)
        if ver:
            return "VERIFIED", f"Adımın çıktısı (sürüm {ver}) kanıt olarak incelendi."
    return "MISSING", "Kanıt eklenmedi (not, bağlantı ya da Proje Eki)."


async def gate(db: AsyncSession, project: Project, task: Task) -> Optional[str]:
    """Onaydan önce: doğrulama eksikse onaylayıcıya gösterilecek metin."""
    st, why = await evaluate(db, project, task)
    if st != "MISSING":
        return None
    v = _v(task)
    return (f"Teslimat doğrulanmadı ({TYPE_TR.get(v.get('type'), v.get('type'))}"
            + (f": {v['method'][:200]}" if v.get("method") else "") + f") — {why}")


async def record_decision(db: AsyncSession, project: Project, task: Task, actor_id, waived_reason: Optional[str]) -> None:
    """Onay anında doğrulama sonucunu sabitler (sonradan değişen test koşusu geçmiş onayı bozmasın)."""
    if not task.verification:
        return
    st, why = await evaluate(db, project, task)
    v = _v(task)
    if waived_reason and st == "MISSING":
        v["waived"] = {"reason": waived_reason[:1000], "by": str(actor_id) if actor_id else None, "at": now().isoformat(), "missing": why}
        v["status"] = "WAIVED"
    else:
        v["status"] = "VERIFIED" if st in ("VERIFIED", "PENDING") else st
        v["note"] = why if st == "VERIFIED" else ("Belirlenen kişinin onayıyla doğrulandı." if st == "PENDING" else why)
    v["decided_at"], v["decided_by"] = now().isoformat(), str(actor_id) if actor_id else None
    task.verification = v


def _cover_tasks(tasks: List[Task]) -> List[Task]:
    return [t for t in tasks if t.status != "CANCELLED" and not t.fix_of_task_id]


async def coverage(db: AsyncSession, project: Project) -> Dict[str, Any]:
    tasks = (await db.execute(select(Task).where(Task.project_id == project.id).order_by(Task.order_index))).scalars().all()
    rows = []
    for t in _cover_tasks(tasks):
        st, why = await evaluate(db, project, t)
        v = _v(t)
        rows.append({"task_id": str(t.id), "title": t.title, "task_status": t.status, "deliverable": t.deliverable,
                     "type": v.get("type"), "type_label": TYPE_TR.get(v.get("type"), "—"), "method": v.get("method"),
                     "status": st, "status_label": STATUS_TR[st], "reason": why, "evidence": v.get("evidence") or [],
                     "measure": v.get("measure"), "checklist": v.get("checklist"), "waived": v.get("waived")})
    total = len(rows)
    counts = {k: sum(1 for r in rows if r["status"] == k) for k in STATUS_TR}
    text = f"{total} teslimattan {counts['VERIFIED']} tanesi doğrulandı"
    extra = []
    if counts["MISSING"]:
        extra.append(f"{counts['MISSING']} tanesinde doğrulama eksik")
    if counts["WAIVED"]:
        extra.append(f"{counts['WAIVED']} tanesi gerekçeyle kabul edildi")
    if counts["PENDING"]:
        extra.append(f"{counts['PENDING']} tanesi insan onayı ya da yöntem bekliyor")
    return {"summary": text + (", " + ", ".join(extra) if extra else ""), "total": total, "counts": counts, "rows": rows}


def completion_problem(cov: Dict[str, Any]) -> Optional[str]:
    """Projenin kabulü: tamamlanan adımların hepsi doğrulanmış ya da gerekçeyle kabul edilmiş olmalı."""
    missing = [r for r in cov["rows"] if r["task_status"] == "DONE" and r["status"] == "MISSING"]
    open_ = [r for r in cov["rows"] if r["task_status"] != "DONE"]
    if not missing and not open_:
        return None
    parts = []
    if missing:
        parts.append(f"{len(missing)} tamamlanmış adımın doğrulaması eksik ({', '.join(r['title'] for r in missing[:4])})")
    if open_:
        parts.append(f"{len(open_)} adım tamamlanmadı")
    return f"{cov['summary']}. " + "; ".join(parts) + "."


# ---------------------------------------------------------------- kayıtlar (sorumlu / onaylayıcı)
async def add_evidence(db: AsyncSession, task: Task, actor_id, kind: str, text: str, url: Optional[str], document_id: Optional[str]) -> Dict[str, Any]:
    v = _v(task)
    ev = list(v.get("evidence") or [])
    if len(ev) >= MAX_EVIDENCE:
        raise ValueError("Bir teslimata en fazla 20 kanıt eklenebilir.")
    item = {"kind": kind, "text": (text or "")[:1000], "url": (url or None), "document_id": document_id,
            "by": str(actor_id), "at": now().isoformat()}
    if kind == "document":
        doc = await db.get(AgentDocument, document_id) if document_id else None
        if not doc or doc.project_id != task.project_id:
            raise LookupError("Proje Eki bulunamadı.")
        item["name"] = doc.original_name
    ev.append(item)
    v["evidence"] = ev
    task.verification = v
    return v


def set_measure(task: Task, actor_id, value: str, unit: Optional[str], note: Optional[str]) -> Dict[str, Any]:
    v = _v(task)
    v["measure"] = {"value": str(value)[:60], "unit": (unit or "")[:30], "note": (note or "")[:500], "by": str(actor_id), "at": now().isoformat()}
    task.verification = v
    return v


def set_checklist(task: Task, actor_id, oks: List[bool]) -> Dict[str, Any]:
    v = _v(task)
    items = list(v.get("checklist") or [])
    for i, it in enumerate(items):
        if i < len(oks):
            items[i] = {**it, "ok": bool(oks[i]), "by": str(actor_id), "at": now().isoformat()}
    v["checklist"] = items
    task.verification = v
    return v


# ---------------------------------------------------------------- yazılım: gevşetilen denetimler
def _strength(check: Dict[str, Any]) -> int:
    """Denetimin 'sıkılığı': beklenti sayısı (durum kodu, metin, seçici, kayıt, adımlardaki beklentiler)."""
    n = sum(1 for k in ("expect_status", "expect_text", "expect_json", "save") if check.get(k) not in (None, "", {}))
    for st in check.get("steps") or []:
        if isinstance(st, dict) and any(k in st for k in ("expect_text", "expect_selector", "wait_for_selector")):
            n += 1
    return n


def loosened_checks(base_json: Optional[str], ref_json: Optional[str]) -> List[Dict[str, Any]]:
    """Ana daldaki (önceden doğrulanmış) recorion.json denetimlerinden adımın dalında silinen ya da beklentisi azalanlar."""
    def load(s):
        try:
            d = json.loads(s or "{}")
            return {str(c.get("name")): c for c in (d.get("checks") or []) if isinstance(c, dict) and c.get("name")}
        except (ValueError, AttributeError):
            return {}
    base, ref = load(base_json), load(ref_json)
    if not base or not ref_json:
        return []
    out = []
    for name, c in base.items():
        if name not in ref:
            out.append({"name": name, "change": "silindi"})
        elif _strength(ref[name]) < _strength(c):
            out.append({"name": name, "change": f"beklenti {_strength(c)} → {_strength(ref[name])}"})
    return out


async def loosened_for_ref(project: Project, ref: str) -> List[Dict[str, Any]]:
    from app.services import code_repo

    if not ref or ref == code_repo.BASE_BRANCH:
        return []

    async def get(r):
        try:
            return (await code_repo.read_file(project, r, "recorion.json"))["content"]
        except Exception:
            return None
    return loosened_checks(await get(code_repo.BASE_BRANCH), await get(ref))
