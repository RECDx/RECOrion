"""
AI personelin iş adımını kendisinin yürütmesi ve kontrol personelinin değerlendirmesi (ADIM 7.2).

produce(): atanan AI personel; rol istemi + 4 katmanlı bilgi + önceki adımların çıktıları + geri bildirimle iş
  adımının çıktısını üretir. Çıktı yeni sürüm artefakt olarak nesne deposuna yazılır ve görev sohbetine düşer.
review(): kontrol personeli (AI) çıktıyı kabul ölçütüne göre değerlendirir: {"passed", "score", "issues", "summary"}.
Her iki işlem de LLM Gateway üzerinden ölçülür ve krediden düşer. Hatalar akışı durdurmaz; sonuç {"ok": False} döner,
akış adımı karantinaya alıp yöneticinin kararını bekler.
"""
import hashlib
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, Artifact, ChatMessage, Project, Task, TaskEvent, Tenant
from app.services import code_repo, knowledge, live, llm_gateway, model_router, sandbox, storage, task_flow
from app.services.llm_gateway import LLMContext, LLMError

logger = logging.getLogger("recorion.agent_work")

MAX_DEP_CHARS = 3000
MAX_OWN_CHARS = 40000  # düzeltmede AI kendi önceki sürümünün tamamını görür
REVIEW_MAX_CHARS = 60000  # kontrol personeli çıktının tamamını değerlendirir
# Senaryo F87 (08.11.2026): devamla parça birleştirme kodda kırılgan (ek yerinde satır bölünüyor, boşluk yutuluyor);
# akışlı çağrı ve ilk token sınırı (#666) kuyrukta takılmayı ayrıca yakaladığından bir çağrı uzun çıktıyı tek
# seferde üretebilir (qwen ~17 token/sn → 12000 token ≈ 12 dk). Daha uzun çıktı yine devamla tamamlanır.
WORK_MAX_TOKENS = 12000
WORK_TIMEOUT = 900
MAX_CONTINUATIONS = 3


def _truncated(result) -> bool:
    """Model çıktısı token sınırında kesildi mi (finish_reason=length)."""
    try:
        return (result.raw.get("choices") or [{}])[0].get("finish_reason") == "length"
    except (AttributeError, IndexError):
        return False


SEAM_MAX_OVERLAP = 400
SEAM_MIN_OVERLAP = 5
FENCE = "`" * 3
# Açık kod bloğunun içinde kesilen çıktının devamı bazen "## Devam" gibi bir başlık ve yeniden açılan blokla başlıyor;
# bunlar dosyanın içine karışmasın diye atılır (en çok 3 başlık/devam satırı + dili ya da yolu olan açılış satırı).
REOPEN_RE = re.compile(r"\A(?:[ \t]*(?:#{1,6}[^\n]*|[^\n`]*[Dd]evam[^\n`]*)?\n){0,3}[ \t]*" + FENCE + r"[\w+#.-]+[^\n`]*\n")


def _in_open_fence(text: str) -> bool:
    return sum(1 for line in text.splitlines() if line.lstrip().startswith(FENCE)) % 2 == 1


def join_pieces(pieces: List[str]) -> str:
    """Devam parçalarını birleştirir. Model kaldığı yerden biraz geriden başlarsa (ör. "...return" + "return patients")
    ek yerindeki örtüşme bir kez yazılır (senaryo F87, 08.11.2026: "return return patients")."""
    out = ""
    for piece in pieces:
        if out and piece and _in_open_fence(out):
            m = REOPEN_RE.match(piece.lstrip("\n"))
            if m:  # satır ortasında kesildiyse araya satır sonu eklenmez; tekrar eden satır başı aşağıda kırpılır
                piece = piece.lstrip("\n")[m.end():]
        if out and piece:
            head = piece.lstrip()
            tail = out.rstrip()
            for k in range(min(SEAM_MAX_OVERLAP, len(tail), len(head)), SEAM_MIN_OVERLAP - 1, -1):
                if tail[-k:] == head[:k]:
                    piece = head[k:]
                    out = tail
                    break
        out += piece
    return out


async def _generate(ctx: LLMContext, messages: List[Dict[str, str]], tooling: Optional[tuple] = None):
    """Çıktıyı üretir; token sınırında kesilirse en fazla MAX_CONTINUATIONS kez devam ettirip parçaları birleştirir.
    tooling = (db, agent, project, task): ilk parça araç döngüsüyle (ADIM 10.2); devam parçaları araçsız."""
    from app.services import tool_gateway

    pieces, credits, result, fallback_from, fallback_model, calls = [], 0.0, None, None, None, []
    for i in range(MAX_CONTINUATIONS + 1):
        # Personelin modeli meşgul/yanıtsızsa paketteki yedek modelle sürer (kullanıcı kararı, 22.10.2026)
        # Yedek modele geçildiyse kesilen çıktının devamı da aynı (yedek) modelle üretilir
        kw = dict(model_code=fallback_model, temperature=0.4, max_tokens=WORK_MAX_TOKENS, timeout=WORK_TIMEOUT, fallback=True)
        if tooling and i == 0:
            db, agent, project, task = tooling
            result, calls = await tool_gateway.chat_with_tools(db, ctx, messages, agent, project, task, **kw)
        else:
            result = await llm_gateway.chat(ctx, messages, **kw)
        if result.fallback_from:
            fallback_from, fallback_model = result.fallback_from, result.model_code  # devam parçaları aynı modelle
        pieces.append(result.content)
        credits += float(result.credits)
        if not _truncated(result):
            break
        await live.thought(ctx.project_id, ctx.task_id, "CONTINUE", f"Çıktı uzun; kaldığı yerden devam ediyor (parça {len(pieces) + 1}).")
        messages = messages + [{"role": "assistant", "content": result.content},
                               {"role": "user", "content": "Çıktın token sınırında kesildi. Tekrar etmeden, tam kaldığın yerden devam et. "
                                "Başlık, açıklama veya \"Devam\" gibi bir giriş yazma; bir kod bloğunun içinde kaldıysan yeni blok "
                                "açmadan doğrudan kodun devamını yaz ve bloğu her zamanki gibi kapat."}]
    return join_pieces(pieces).strip(), result, len(pieces), round(credits, 4), fallback_from, calls


def artifact_key(task: Task, version: int) -> str:
    return f"artifacts/{task.project_id}/{task.id}/v{version}.md"


async def latest_artifact(db: AsyncSession, task_id) -> Optional[Artifact]:
    return (await db.execute(select(Artifact).where(Artifact.task_id == task_id).order_by(Artifact.version.desc()).limit(1))).scalars().first()


async def artifact_text(art: Optional[Artifact], limit: int) -> str:
    if not art or not art.storage_path:
        return ""
    try:
        return (await storage.get_object(art.storage_path)).decode("utf-8", "replace")[:limit]
    except Exception as exc:  # depo erişilemezse çıktı bağlamı eksik kalır, iş durmaz
        logger.warning("Artefakt okunamadı (%s): %s", art.id, exc)
        return ""


async def _load(db: AsyncSession, task_id):
    task = await db.get(Task, uuid.UUID(str(task_id)))
    project = await db.get(Project, task.project_id)
    tenant = await db.get(Tenant, project.tenant_id)
    return task, project, tenant


TEST_INSTRUCTIONS = (
    "\n\nSen bu projenin test uzmanısın ve RECOrion Kod Çalıştırma Ortamı'nı kullanıyorsun (ADIM 16.2): çıktını teslim ettiğin anda "
    "adımın dalı (önceki adımlarda ana dala birleşen kod + senin dosyaların) yalıtılmış bir kapta GERÇEKTEN çalıştırılır ve sonuçları "
    "sana gösterilir. Bu yüzden çalıştırılabilir testler yaz: Python için tests/ altında pytest dosyaları (gerekirse "
    "requirements.txt'e test bağımlılığı ekle); JavaScript için package.json'daki \"test\" betiğiyle çalışan testler "
    "(ör. node --test). Mevcut kodu depodaki yollarıyla içe aktar; var olmayan modül uydurma. Testler internetsiz çalışır: dış "
    "servise, gerçek veritabanı sunucusuna bağlanma (SQLite/bellek içi kullan). İstersen kökte scripts/recorion_test.sh betiği "
    "yazabilirsin; varsa o da çalıştırılır. Test planını ve hangi testin neyi doğruladığını dokümanda kısaca anlat. "
    "Uygulama kodunu (src/ vb.) değiştiremezsin: yalnız test dosyaları, conftest, test bağımlılıkları, recorion.json, README ve "
    "scripts/recorion_test.sh depoya yazılır. Uygulamada bir hata bulursan testte ATLATMA (farklı şifreleme, sahte nesneyle asıl "
    "yolu geçme, beklentiyi gevşetme yok): testi doğru bırak, hatayı ve olası düzeltmeyi raporla; testler kalırsa sistem düzeltme "
    "turunu ilgili geliştiriciye açar.")

# İSTEK #734: test ve kabul adımı uygulamayı gerçekten açıp dener (duman testi)
SMOKE_INSTRUCTIONS = (
    "\n\nDUMAN TESTİ (zorunlu): Birim testleri yetmez; uygulama talimatla kurulup AÇILMALI ve temel akış denenmeli. Deponun kökündeki "
    "recorion.json dosyasını (```json recorion.json bloğuyla) yaz veya güncelle; Kod Çalıştırma Ortamı bağımlılıkları kurduktan sonra bu dosyadaki komutlarla "
    "uygulamayı internetsiz açar ve denetimleri çalıştırır. Biçim: {\"services\": [{\"name\": \"api\", \"dir\": \".\", "
    "\"start\": \"uvicorn src.main:app --host 127.0.0.1 --port 8000\", \"port\": 8000, \"ready\": \"/docs\"}], \"checks\": ["
    "{\"name\": \"Giriş\", \"type\": \"http\", \"service\": \"api\", \"method\": \"POST\", \"path\": \"/token\", "
    "\"form\": {\"username\": \"...\", \"password\": \"...\"}, \"expect_status\": 200, \"save\": {\"token\": \"access_token\"}}, "
    "{\"name\": \"Liste\", \"type\": \"http\", \"service\": \"api\", \"path\": \"/...\", \"bearer\": \"{token}\", \"expect_status\": 200}, "
    "{\"name\": \"Arayüzden giriş\", \"type\": \"browser\", \"service\": \"api\", \"path\": \"/\", \"steps\": [{\"fill\": \"#username\", "
    "\"value\": \"...\"}, {\"click\": \"button[type=submit]\"}, {\"expect_text\": \"girişten sonra görünen metin\"}]}]}. "
    "Kurallar: başlatma komutu README'deki komutla aynı olsun; ilk açılışta gereken klasör/veritabanı/örnek veri uygulamanın kendisi "
    "tarafından oluşturulsun; web arayüzü varsa en az bir 'browser' denetimiyle gerçek arayüzden giriş ve bir temel işlem denensin "
    "(seçiciler depodaki HTML ile birebir aynı olmalı); arayüz API'ye hangi adresten bağlanıyorsa o adres gerçekten çalışmalı (ayrı "
    "port ise CORS ve adres ayarı tutarlı olmalı; en sağlamı arayüzü backend'in aynı adresinden sunmak). Kökte README.md kurulum, "
    "çalıştırma, örnek giriş bilgileri ve test komutlarıyla eksiksiz olsun.")


def _system(actor: Actor, tenant: Tenant, has_repo: bool = False, test_runner=False) -> str:
    """test_runner: "test" (test uzmanı), "accept" (kabul/teslim adımı) veya False."""
    base = actor.system_prompt or f"Sen {tenant.name} şirketinin {actor.role} unvanlı AI personelisin."
    repo = ("\n\nBu projenin kod deposu var (ADIM 8.5): yazdığın her kaynak kod veya yapılandırma dosyasını ayrı bir kod "
            "bloğunda ver ve bloğun açılış satırına dili ve depodaki dosya yolunu yaz (ör. ```python src/app/main.py). "
            "Bu dosyalar adımın dalına commit edilir; yol belirtmediğin kod blokları yalnızca dokümanda kalır. "
            "Kodun içine uzun açıklama veya düşünce yorumu yazma; tasarım kararlarını kod bloğunun dışında kısaca anlat, "
            "her dosyayı baştan sona eksiksiz yaz.") if has_repo else ""
    repo += (TEST_INSTRUCTIONS if test_runner == "test" else "") + SMOKE_INSTRUCTIONS if (has_repo and test_runner) else ""
    return (f"{base}\n\nRECOrion iş akışında sana atanan bir iş adımını yürütüyorsun. Çıktın doğrudan teslim edilecek iş "
            "ürünüdür (doküman, analiz, kod, plan vb.): eksiksiz, uygulanabilir ve Markdown biçiminde yaz. Odaklı ol: gereksiz "
            "tekrar ve dolgu yazma; çoğu iş adımı için 600-1500 kelime yeterlidir. Bilmediğin bilgiyi "
            "uydurma; tarih, adım numarası, sürüm, kişi adı ve kullanıcı/şifre gibi bilgileri yalnız sana verilenlerden ve depodaki "
            "koddan al (F108). Varsayımlarını ve açık soruları çıktının sonunda 'Varsayımlar ve açık sorular' başlığıyla belirt." + repo)


async def produce(db: AsyncSession, task_id, feedback: Optional[str] = None) -> Dict[str, Any]:
    task, project, tenant = await _load(db, task_id)
    agent = await db.get(Actor, task.assignee_actor_id) if task.assignee_actor_id else None
    if not agent or agent.actor_type != "AI_AGENT":
        return {"ok": False, "error": "İş adımına atanmış bir AI personel yok."}
    # Önceki adımların (bağımlılıkların) son çıktıları
    dep_blocks: List[str] = []
    for dep_id in task.depends_on or []:
        dep = await db.get(Task, uuid.UUID(str(dep_id)))
        if dep:
            text = await artifact_text(await latest_artifact(db, dep.id), MAX_DEP_CHARS)
            if text:
                dep_blocks.append(f"## {dep.title}\n{text}")
    # F98: depo etkinse ana daldaki gerçek kod (özet değil) bağlama girer
    repo_context = await code_repo.context_for_ai(project) if code_repo.active(project) else ""
    previous = await latest_artifact(db, task.id)
    own = await artifact_text(previous, MAX_OWN_CHARS)
    scope = await knowledge.scope_for_agent(db, tenant.id, agent.id, project.id)
    hits = await knowledge.retrieve(scope, f"{task.title}\n{task.description or ''}"[:2000], limit=6)
    # Mevzuat paketleri (ADIM 11.2): adımla ilgili, şirketin açtığı ve uzman kontrolünden geçmiş özetler
    from app.services import regulations
    reg_context, _ = await regulations.context_for(
        db, tenant.id, f"{task.title}\n{task.description or ''}\n{task.acceptance_criteria or ''}")
    await live.thought(project.id, task.id, "ANALYSIS", f"{agent.display_name}: bilgi katmanlarında {len(hits)} kaynak, "
                       f"{len(dep_blocks)} önceki adım çıktısı bulundu" + ("; düzeltme isteği okunuyor." if feedback else "."))
    await live.thought(project.id, task.id, "WRITING", f"{agent.display_name} {'düzeltilmiş ' if feedback else ''}çıktıyı yazıyor…")
    latest_run = ""
    if task.fix_kind == "FIX":  # F109: düzeltme adımı açıldığı andaki değil en güncel koşu sonucuyla çalışır
        lr = await sandbox.latest_lineage_run(db, task)
        if lr:
            latest_run = ("\n# En güncel test koşusu (sistem; açıklamadaki eski sonuçtan önceliklidir)\n" + sandbox.report_md(lr)[:5000]
                          + ("\n\nNot: en son koşuda testler GEÇTİ; yalnız gerçekten kalan bir sorun varsa düzelt." if lr.status == "PASSED" else "")
                          + "\n")
    prompt = f"""# Proje
{project.name}
İsterler:
{(project.requirements or '-')[:5000]}

# İş adımı
Başlık: {task.title}
Sıra: projenin {task.order_index or '-'}. adımı
Bugünün tarihi: {datetime.now(ZoneInfo('Europe/Istanbul')).strftime('%d.%m.%Y')}
Ne yapılacak: {task.description or '-'}
Kabul ölçütü: {task.acceptance_criteria or '-'}
{latest_run}{knowledge.format_context(hits, max_chars=6000)}{reg_context}
{repo_context}# Önceki adımların çıktıları
{chr(10).join(dep_blocks) or 'yok'}

# Bu adımın önceki sürümü
{own or 'yok (ilk sürüm)'}

# Düzeltilmesi istenenler
{feedback or 'yok'}

Bu iş adımının {'düzeltilmiş ' if feedback else ''}çıktısını şimdi tam olarak yaz."""
    try:
        content, result, parts, credits, fallback_from, tool_calls = await _generate(
            LLMContext(tenant_id=tenant.id, purpose="AGENT_CHAT", actor_id=agent.id, task_id=task.id, project_id=project.id,
                       task_type=model_router.classify(task.title, task.description, task.acceptance_criteria, job_title=agent.role)),
            [{"role": "system", "content": _system(agent, tenant, code_repo.active(project), _runs_tests(project, agent, task))},
             {"role": "user", "content": prompt}],
            tooling=(db, agent, project, task))
    except LLMError as exc:
        return {"ok": False, "error": exc.message}
    except Exception as exc:
        logger.exception("AI personel çalışması başarısız")
        return {"ok": False, "error": f"AI personel çalışamadı: {exc}"}
    if not content:
        return {"ok": False, "error": "AI personel boş çıktı üretti."}
    version = (previous.version + 1) if previous else 1
    data = content.encode("utf-8")
    key = artifact_key(task, version)
    await storage.put_object(key, data, "text/markdown; charset=utf-8")
    art = Artifact(task_id=task.id, name=f"{task.title} (sürüm {version})"[:255], artifact_type="DOCUMENT", storage_path=key,
                   version=version, content_hash=hashlib.sha256(data).hexdigest(), produced_by_actor_id=agent.id,
                   approval_status="SUBMITTED")
    db.add(art)
    db.add(ChatMessage(tenant_id=tenant.id, project_id=project.id, task_id=task.id, sender_actor_id=agent.id, role="assistant",
                       content=content, thought_process=result.thought, message_type="CHAT"))
    await db.flush()
    note = f"Sürüm {version} üretildi." + (" Asıl model yanıt vermediği için yedek model kullanıldı." if fallback_from else "")
    await task_flow.log(db, project, task, "AI_OUTPUT", agent.id, note,
                        {"artifact_id": str(art.id), "version": version, "model": result.public_model, "credits": credits, "parts": parts,
                         "fallback_used": bool(fallback_from),
                         "tool_calls": [{"id": str(c.id), "tool": c.tool, "status": c.status} for c in tool_calls]})
    runs = _runs_tests(project, agent, task)
    keep = code_repo.is_test_path if runs == "test" else None  # F104: test uzmanı yalnız test dosyalarını commit eder
    dropped = await code_repo.after_output(db, project, task, version, content, agent.display_name, keep)  # depo varsa adımın dalına commit
    if dropped:
        warn = ("\n\n_Sistem: test uzmanı uygulama kodunu değiştiremez; şu dosyalar depoya yazılmadı: "
                + ", ".join(f"`{d}`" for d in dropped[:15]) + ". Uygulamadaki hata düzeltme turunda geliştiriciye gider._")
        content += warn
        data = content.encode("utf-8")
        await storage.put_object(key, data, "text/markdown; charset=utf-8")
        art.content_hash = hashlib.sha256(data).hexdigest()
    if runs:
        # Test Uzmanı: dal Kod Çalıştırma Ortamı'nda gerçekten çalışır; sonuç ve AI değerlendirmesi çıktıya eklenir
        extra = await _with_test_run(db, project, task, tenant, agent)
        content = f"{content}\n\n{extra}"
        data = content.encode("utf-8")
        await storage.put_object(key, data, "text/markdown; charset=utf-8")
        art.content_hash = hashlib.sha256(data).hexdigest()
        # Görev sohbeti yalnız eklemeli: sonuç ayrı mesaj olarak düşer
        db.add(ChatMessage(tenant_id=tenant.id, project_id=project.id, task_id=task.id, sender_actor_id=agent.id, role="assistant",
                           content=extra, message_type="CHAT"))
    await db.commit()
    if runs:  # düzeltme turu açıldıysa/kapandıysa proje akışı hemen görsün
        await sandbox.wake_project(project)
    return {"ok": True, "artifact_id": str(art.id), "version": version, "actor_id": str(agent.id)}


def _runs_tests(project: Project, agent: Actor, task: Optional[Task] = None):
    """Adım teslim edilince kod gerçekten çalıştırılır mı: test uzmanı ("test") veya kabul/teslim adımı ("accept", #734)."""
    if not (sandbox.enabled() and code_repo.active(project)):
        return False
    if sandbox.is_test_role(agent.role):
        return "test"
    return "accept" if task is not None and sandbox.is_acceptance_step(task) else False


async def _with_test_run(db: AsyncSession, project: Project, task: Task, tenant: Tenant, agent: Actor) -> str:
    await live.thought(project.id, task.id, "ANALYSIS", f"{agent.display_name}: testler Kod Çalıştırma Ortamı'nda çalıştırılıyor…")
    run = await sandbox.start(db, project, task.repo_branch or code_repo.BASE_BRANCH, agent.id, task)
    await db.commit()  # koşu Testler sekmesinde "Çalışıyor" görünsün
    run = await sandbox.finish(db, project, run, task)
    facts = sandbox.report_md(run)
    await live.thought(project.id, task.id, "WRITING", f"{agent.display_name} gerçek test sonuçlarını değerlendiriyor…")
    try:
        res = await llm_gateway.chat(
            LLMContext(tenant_id=tenant.id, purpose="AGENT_CHAT", actor_id=agent.id, task_id=task.id, project_id=project.id, task_type="ANALYSIS"),
            [{"role": "system", "content": _system(agent, tenant)},
             {"role": "user", "content": f"Adımın kodu (testler ve duman testi) RECOrion Kod Çalıştırma Ortamı'nda çalıştırıldı. Gerçek sonuç:\n\n{facts}\n\n"
                                         "Bu sonuca göre kısa bir test değerlendirmesi yaz (150-400 kelime, Markdown, başlık kullanma): neler "
                                         "doğrulandı, kalan testlerin olası nedeni (uygulama hatası mı test hatası mı), geliştiriciye somut "
                                         "düzeltme önerileri ve son satırda 'Karar: Kabul' ya da 'Karar: Düzeltme gerekli'. Sonucu olduğundan "
                                         "iyi gösterme; çalıştırılamadıysa bunu açıkça yaz."}],
            temperature=0.2, max_tokens=1500, timeout=240, fallback=True)
        evaluation = (res.content or "").strip()
    except LLMError as exc:
        evaluation = f"_Değerlendirme yazılamadı: {exc.message}_"
    loop = await sandbox.schedule_fix_loop(db, project, task, run)  # kalan testler → geliştiriciye düzeltme + yeniden test
    return f"{facts}\n\n## Test Uzmanı değerlendirmesi (gerçek koşuya göre)\n\n{evaluation}" + (f"\n\n{loop}" if loop else "")


REVIEW_MAX_TOKENS = 3000


async def _review_skipped(db: AsyncSession, project, task, reviewer, reason: str) -> Dict[str, Any]:
    """Değerlendirme yapılamadı: adım sessizce geçmez, geçmişe kaydedilir ve karar insan onaylayıcıya kalır."""
    await task_flow.log(db, project, task, "REVIEW_SKIPPED", reviewer.id, reason[:1000])
    await db.commit()
    return {"ok": False, "error": reason}


def _parse(text: str) -> Dict[str, Any]:
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


async def review(db: AsyncSession, task_id) -> Dict[str, Any]:
    """Kontrol personeli son çıktıyı değerlendirir. Değerlendirme yapılamazsa {"ok": False} (akış insana bırakır)."""
    task, project, tenant = await _load(db, task_id)
    reviewer = await db.get(Actor, task.reviewer_actor_id) if task.reviewer_actor_id else None
    if not reviewer:
        return {"ok": False, "error": "Kontrol personeli tanımlı değil."}
    art = await latest_artifact(db, task.id)
    text = await artifact_text(art, REVIEW_MAX_CHARS)
    if not text:
        return {"ok": False, "error": "Değerlendirilecek çıktı bulunamadı."}
    # F103: testler kaldı ve düzeltme turu açık → kontrol personeli bu adımı "testler kalıyor" diye reddetmez (kilitlenme);
    # testlerin kalitesini proje yöneticisi onayda görür, kod düzeltme turunda düzelir.
    open_fix = (await db.execute(select(Task).where(Task.fix_of_task_id == sandbox.root_of(task), Task.fix_kind == "FIX",
                                                    Task.status.notin_(task_flow.CLOSED)).limit(1))).scalar_one_or_none()
    if open_fix:
        note = (f"Kontrol atlandı: testler kaldı ve '{open_fix.title}' düzeltme turu açık. Kalan testler bu adımın ret sebebi "
                "sayılmaz; karar proje yöneticisinde.")
        await task_flow.log(db, project, task, "REVIEW_SKIPPED", reviewer.id, note)
        await db.commit()
        return {"ok": True, "passed": True, "score": None, "note": note, "actor_id": str(reviewer.id)}
    system = (reviewer.system_prompt or f"Sen {tenant.name} şirketinin {reviewer.role} unvanlı AI personelisin.") + (
        "\n\nRECOrion iş akışında kontrol personelisin: teslim edilen çıktıyı iş adımının kabul ölçütüne göre tarafsız "
        "ve somut değerlendir. Yalnızca gerçek eksik ve hataları yaz; küçük üslup tercihlerini ret sebebi yapma. "
        "Senden sonra insan onaylayıcı (proje yöneticisi) çıktıyı ayrıca onaylayacak: yönetici onayı, imza, toplantı gibi "
        "insanların yapacağı işlemleri eksik sayma; yalnızca çıktının içeriğini değerlendir. "
        # F91: hedef kaydırma yok — ret yalnız kabul ölçütünü karşılamayan ya da gerçekten bozuk olan şey için
        "RET SEBEBİ (issues) yalnızca şunlardır: kabul ölçütünün karşılanmaması, çalışmayan/hatalı içerik (bug, eksik zorunlu "
        "bölüm, güvenlik açığı) ve önceki değerlendirmende istenip hâlâ düzeltilmemiş maddeler. Kabul ölçütünde olmayan yeni "
        "beklenti, iyileştirme önerisi, üslup ve 'daha iyi olurdu' türü konuları issues'a değil notes'a yaz; bunlar adımı "
        "geri çevirmez. Önceki değerlendirmende istediklerin karşılandıysa ve engelleyici yeni hata yoksa passed=true ver.")
    prior = (await db.execute(select(TaskEvent.note).where(TaskEvent.task_id == task.id, TaskEvent.kind == "REVIEW_FAILED")
                              .order_by(TaskEvent.created_at.desc()).limit(2))).scalars().all()
    prior_text = "\n\n".join(f"- {(n or '').strip()[:1500]}" for n in reversed(prior)) or "yok (ilk değerlendirme)"
    prompt = f"""# İş adımı
Başlık: {task.title}
Ne yapılacak: {task.description or '-'}
Kabul ölçütü: {task.acceptance_criteria or '-'}

# Önceki değerlendirmelerinde istediklerin (yalnız bunların düzelip düzelmediğine bak; yeni ret ölçütü ekleme)
{prior_text}

# Teslim edilen çıktı (sürüm {art.version})
{text}

Sadece şu JSON'u döndür (issues en fazla 6, notes en fazla 4 madde, her biri en fazla 200 karakter; başka metin yazma):
{{"passed": true|false, "score": 0-100, "issues": ["ret sebebi: kabul ölçütü ihlali veya gerçek hata"],
  "notes": ["engelleyici olmayan öneri"], "summary": "1-2 cümle değerlendirme"}}"""
    ctx = LLMContext(tenant_id=tenant.id, purpose="AGENT_CHAT", actor_id=reviewer.id, task_id=task.id, project_id=project.id,
                     task_type="STRUCTURED")  # değerlendirme JSON döner (ADIM 11.4 yönlendirme)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    verdict, result, last_error = None, None, None
    await live.thought(project.id, task.id, "REVIEW", f"{reviewer.display_name} sürüm {art.version} çıktısını kabul ölçütüne göre değerlendiriyor…")
    try:
        # Uzun çıktıda bulgu listesi uzayıp yanıt kesilebilir: okunamazsa bir kez kısa ve geçerli JSON istenir
        for attempt in range(2):
            result = await llm_gateway.chat(ctx, messages, temperature=0.2, max_tokens=REVIEW_MAX_TOKENS, timeout=180, fallback=True)
            try:
                verdict = _parse(result.content)
                break
            except (ValueError, KeyError) as exc:
                last_error = exc
                messages = messages + [{"role": "assistant", "content": result.content[:4000]},
                                       {"role": "user", "content": "Yanıtın geçerli JSON değildi veya kesildi. Yalnızca istenen JSON'u, "
                                                                   "en fazla 5 kısa maddeyle tekrar yaz."}]
    except LLMError as exc:
        return await _review_skipped(db, project, task, reviewer, exc.message)
    if verdict is None:
        return await _review_skipped(db, project, task, reviewer, f"Kontrol personelinin değerlendirmesi okunamadı ({last_error}).")
    issues = [str(i)[:500] for i in (verdict.get("issues") or [])][:10]
    notes = [str(i)[:500] for i in (verdict.get("notes") or [])][:6]
    passed = verdict.get("passed") is True or not issues  # ret sebebi yazılmadıysa ret yok (F91)
    try:
        score = max(0, min(100, int(verdict.get("score") or 0)))
    except (TypeError, ValueError):
        score = 0
    summary = str(verdict.get("summary") or "")[:1000]
    note = summary + ("\n- " + "\n- ".join(issues) if issues and not passed else "") + (
        "\nÖneriler (ret sebebi değil):\n- " + "\n- ".join(notes) if notes else "")
    await task_flow.log(db, project, task, "REVIEW_PASSED" if passed else "REVIEW_FAILED", reviewer.id, note.strip() or None,
                        {"score": score, "version": art.version, "artifact_id": str(art.id), "model": result.public_model,
                         "fallback_used": bool(result.fallback_from)})
    await db.commit()
    return {"ok": True, "passed": passed, "score": score, "note": note.strip(), "actor_id": str(reviewer.id)}

