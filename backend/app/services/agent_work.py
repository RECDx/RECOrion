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
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, Artifact, ChatMessage, Project, Task, Tenant
from app.services import code_repo, knowledge, live, llm_gateway, model_router, storage, task_flow
from app.services.llm_gateway import LLMContext, LLMError

logger = logging.getLogger("recorion.agent_work")

MAX_DEP_CHARS = 3000
MAX_OWN_CHARS = 40000  # düzeltmede AI kendi önceki sürümünün tamamını görür
REVIEW_MAX_CHARS = 60000  # kontrol personeli çıktının tamamını değerlendirir
# Her çağrı daha kısa parça üretir (uzun bağlamlı adımlarda zaman aşımını önler); uzun çıktı devamla tamamlanır
WORK_MAX_TOKENS = 4000
WORK_TIMEOUT = 360
MAX_CONTINUATIONS = 3


def _truncated(result) -> bool:
    """Model çıktısı token sınırında kesildi mi (finish_reason=length)."""
    try:
        return (result.raw.get("choices") or [{}])[0].get("finish_reason") == "length"
    except (AttributeError, IndexError):
        return False


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
                               {"role": "user", "content": "Çıktın token sınırında kesildi. Tekrar etmeden, tam kaldığın yerden devam et."}]
    return "".join(pieces).strip(), result, len(pieces), round(credits, 4), fallback_from, calls


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


def _system(actor: Actor, tenant: Tenant, has_repo: bool = False) -> str:
    base = actor.system_prompt or f"Sen {tenant.name} şirketinin {actor.role} unvanlı AI personelisin."
    repo = ("\n\nBu projenin kod deposu var (ADIM 8.5): yazdığın her kaynak kod veya yapılandırma dosyasını ayrı bir kod "
            "bloğunda ver ve bloğun açılış satırına dili ve depodaki dosya yolunu yaz (ör. ```python src/app/main.py). "
            "Bu dosyalar adımın dalına commit edilir; yol belirtmediğin kod blokları yalnızca dokümanda kalır.") if has_repo else ""
    return (f"{base}\n\nRECOrion iş akışında sana atanan bir iş adımını yürütüyorsun. Çıktın doğrudan teslim edilecek iş "
            "ürünüdür (doküman, analiz, kod, plan vb.): eksiksiz, uygulanabilir ve Markdown biçiminde yaz. Odaklı ol: gereksiz "
            "tekrar ve dolgu yazma; çoğu iş adımı için 600-1500 kelime yeterlidir. Bilmediğin bilgiyi "
            "uydurma; varsayımlarını ve açık soruları çıktının sonunda 'Varsayımlar ve açık sorular' başlığıyla belirt." + repo)


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
    prompt = f"""# Proje
{project.name}
İsterler:
{(project.requirements or '-')[:5000]}

# İş adımı
Başlık: {task.title}
Ne yapılacak: {task.description or '-'}
Kabul ölçütü: {task.acceptance_criteria or '-'}
{knowledge.format_context(hits, max_chars=6000)}{reg_context}
# Önceki adımların çıktıları
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
            [{"role": "system", "content": _system(agent, tenant, code_repo.active(project))}, {"role": "user", "content": prompt}],
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
    await code_repo.after_output(db, project, task, version, content, agent.display_name)  # depo varsa adımın dalına commit
    await db.commit()
    return {"ok": True, "artifact_id": str(art.id), "version": version, "actor_id": str(agent.id)}


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
    system = (reviewer.system_prompt or f"Sen {tenant.name} şirketinin {reviewer.role} unvanlı AI personelisin.") + (
        "\n\nRECOrion iş akışında kontrol personelisin: teslim edilen çıktıyı iş adımının kabul ölçütüne göre tarafsız "
        "ve somut değerlendir. Yalnızca gerçek eksik ve hataları yaz; küçük üslup tercihlerini ret sebebi yapma. "
        "Senden sonra insan onaylayıcı (proje yöneticisi) çıktıyı ayrıca onaylayacak: yönetici onayı, imza, toplantı gibi "
        "insanların yapacağı işlemleri eksik sayma; yalnızca çıktının içeriğini değerlendir.")
    prompt = f"""# İş adımı
Başlık: {task.title}
Ne yapılacak: {task.description or '-'}
Kabul ölçütü: {task.acceptance_criteria or '-'}

# Teslim edilen çıktı (sürüm {art.version})
{text}

Sadece şu JSON'u döndür (en fazla 8 madde, her biri en fazla 200 karakter; başka metin yazma):
{{"passed": true|false, "score": 0-100, "issues": ["düzeltilmesi gereken somut eksik/hata"], "summary": "1-2 cümle değerlendirme"}}"""
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
    passed = verdict.get("passed") is True
    try:
        score = max(0, min(100, int(verdict.get("score") or 0)))
    except (TypeError, ValueError):
        score = 0
    summary = str(verdict.get("summary") or "")[:1000]
    note = summary + ("\n- " + "\n- ".join(issues) if issues else "")
    await task_flow.log(db, project, task, "REVIEW_PASSED" if passed else "REVIEW_FAILED", reviewer.id, note.strip() or None,
                        {"score": score, "version": art.version, "artifact_id": str(art.id), "model": result.public_model,
                         "fallback_used": bool(result.fallback_from)})
    await db.commit()
    return {"ok": True, "passed": passed, "score": score, "note": note.strip(), "actor_id": str(reviewer.id)}

