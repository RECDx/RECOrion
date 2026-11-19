"""
İSTEK #749 — Beyin AI keşif görüşmesi ve Proje Tanım Belgesi.

Beyin AI, plandan önce bir iş analisti gibi proje yöneticisiyle görüşür: sektörden bağımsız soru iskeleti (amaç ve başarı
ölçütü, paydaşlar ve kullanıcılar, kapsam içi/dışı, kısıtlar, teslimatlar ve kabul, riskler ve varsayımlar) + şirketin
sektörüne özgü sorular. Her turda yanıtlarla Proje Tanım Belgesi güncellenir ve olgunluk puanı (0–100) ile eksikler verilir.
Belge proje yöneticisince onaylanmadan Beyin AI plan önermez; puan eşiğin altındaysa onay gerekçe ister. Keşif gerekçeyle
atlanabilir (kayda geçer). Durum projects.settings['discovery'] içinde tutulur.
"""
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Tenant
from app.services import llm_gateway
from app.services import projects as psvc
from app.services.llm_gateway import LLMContext

logger = logging.getLogger("recorion.discovery")

THRESHOLD = 70  # bu puanın altında onay gerekçe ister
MAX_ROUNDS = 8
MAX_QUESTIONS = 5
SKELETON = [
    ("Amaç", "Proje bitince neyin değişmiş olması gerekiyor, nasıl ölçülecek?"),
    ("Paydaşlar", "Kim kullanacak, kim onaylayacak, kim etkilenecek?"),
    ("Kapsam", "Neler kapsam içinde, neler kesinlikle dışında?"),
    ("Kısıtlar", "Bütçe, süre, mevzuat, mevcut sistemler ve veriler"),
    ("Teslimatlar", "Somut olarak ne teslim edilecek, kabulü nasıl yapılacak?"),
    ("Riskler", "Riskler ve varsayımlar"),
    # #754 deneme seti (kurs kaydı 66,5): genel sorularda kalıp işin kurallarını hiç sormuyordu
    ("İş kuralları", "İşin temel nesneleri ve kuralları: ne sunuluyor/satılıyor (ürün, hizmet, program, tür), kapasite/kontenjan, "
                     "fiyat, indirim, taksit ve ödeme koşulları, kimlerin yararlanabileceği (yaş, veli/vasi, uygunluk), "
                     "sınıflandırma/yerleştirme/onay kuralları, istisnalar"),
]
CHARTER_KEYS = ("goal", "success_criteria", "stakeholders", "users_roles", "scope_in", "scope_out", "constraints",
                "deliverables", "workflows", "risks", "assumptions", "open_questions")


def state(project: Project) -> Dict[str, Any]:
    d = dict(((project.settings or {}).get("discovery") or {}))
    d.setdefault("rounds", [])
    d.setdefault("pending", [])
    d.setdefault("charter", {})
    d.setdefault("maturity", {"score": 0, "missing": []})
    d.setdefault("status", "NOT_STARTED")  # NOT_STARTED, IN_PROGRESS, APPROVED, SKIPPED
    return d


def _save(project: Project, d: Dict[str, Any]) -> None:
    project.settings = {**(project.settings or {}), "discovery": d}


def _editable(project: Project) -> None:
    if project.status not in ("DRAFT", "PLANNING"):
        raise HTTPException(status_code=409, detail="Keşif yalnız taslak veya planlama aşamasındaki projede yapılır.")


def ready_for_plan(project: Project) -> Optional[str]:
    """Plan önermeye engel varsa metni; yoksa None. Case'ler ve şablondan/toplantıdan gelen projeler muaf."""
    if project.kind == "CASE" or (project.plan or {}).get("from_template") or (project.plan or {}).get("from_meeting"):
        return None
    d = state(project)
    if d["status"] in ("APPROVED", "SKIPPED"):
        return None
    return ("Önce Keşif & Tanım sekmesinde Beyin AI'nın sorularını yanıtlayıp Proje Tanım Belgesini onaylayın "
            "(ya da gerekçe yazarak keşfi atlayın). Plan, onaylı tanım belgesine göre kurulur.")


def charter_text(project: Project, limit: int = 8000) -> str:
    """Plan ve AI personel istemleri için onaylı tanım belgesi (yoksa boş)."""
    d = state(project)
    if d["status"] != "APPROVED" or not d["charter"]:
        return ""
    return json.dumps(d["charter"], ensure_ascii=False)[:limit]


def _parse(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text[text.find("{"): text.rfind("}") + 1])


def _clean_charter(c: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in CHARTER_KEYS:
        v = c.get(k)
        if k == "deliverables":
            out[k] = [{"name": str(x.get("name") or "")[:200], "acceptance": str(x.get("acceptance") or "")[:600],
                       "verification": str(x.get("verification") or "")[:300]}
                      for x in (v or []) if isinstance(x, dict) and x.get("name")][:40]
        elif k == "goal":
            out[k] = str(v or "")[:1500]
        else:
            out[k] = [str(x)[:500] for x in (v or []) if str(x).strip()][:30] if isinstance(v, list) else ([str(v)[:500]] if v else [])
    return out


async def run_round(db: AsyncSession, project: Project, answers: List[Dict[str, str]], note: Optional[str] = None) -> Dict[str, Any]:
    """Yanıtları işler, tanım belgesini ve olgunluk puanını günceller, sıradaki soruları üretir."""
    _editable(project)
    if not (project.requirements or "").strip():
        raise HTTPException(status_code=422, detail="Önce projenin isterlerini yazın; keşif isterlerden başlar.")
    d = state(project)
    if len(d["rounds"]) >= MAX_ROUNDS:
        raise HTTPException(status_code=409, detail=f"Keşif en fazla {MAX_ROUNDS} tur sürer; tanım belgesini onaylayın ya da düzenleyin.")
    asked = {q["id"]: q for q in d["pending"]}
    qa = [{"id": a.get("id"), "topic": asked.get(a.get("id"), {}).get("topic", ""), "question": asked.get(a.get("id"), {}).get("text", ""),
           "answer": str(a.get("answer") or "").strip()[:3000]} for a in answers if a.get("id") in asked]
    skipped = [asked[q]["text"] for q in asked if q not in {x["id"] for x in qa if x["answer"]}]
    tenant = await db.get(Tenant, project.tenant_id)
    sectors = ", ".join(str(s) for s in (tenant.sectors or [])) or "belirtilmemiş"
    asked_before = "\n".join(f"- {x.get('question')}" for x in [*(y for r in d["rounds"] for y in r.get("qa", [])), *qa] if x.get("question"))
    history = "\n".join(f"- [{x['topic']}] {x['question']} → {x['answer']}" for r in d["rounds"] for x in r.get("qa", []) if x.get("answer"))
    now_qa = "\n".join(f"- [{x['topic']}] {x['question']} → {x['answer'] or '(yanıtlanmadı)'}" for x in qa)
    skeleton = "\n".join(f"- {t}: {q}" for t, q in SKELETON)
    from app.services import web_research  # #750: yöneticinin onayladığı web araştırmalarının kaynaklı bulguları

    research = await web_research.context_text(db, project)
    from app.services import sector_packs

    pack, _ = await sector_packs.for_project(db, project, tenant)
    already = [x.get("question") or "" for r in d["rounds"] for x in r.get("qa", [])] + [q.get("text") or "" for q in d["pending"]]
    pack_text = sector_packs.discovery_context(pack, tenant, already)
    pack_block = f"\n{pack_text}\n" if pack_text else ""
    prompt = f"""Sen {tenant.name} şirketinin Beyin AI'sısın ve bir iş analisti gibi proje yöneticisiyle {'Case' if project.kind == 'CASE' else 'proje'} keşif görüşmesi yapıyorsun.
Amaç: plan yapılmadan önce işin ne olduğunu netleştirmek. Kısa brifle başlayan yöneticinin düşünmediği konuları sen getirirsin.
Bu yalnız yazılım için değildir; şirketin sektörüne ve işin türüne uygun sorular sor (üretim, hizmet, sağlık, kalite, ERP, kampanya…).

# Sektörden bağımsız soru iskeleti (hepsi kapsanmalı)
{skeleton}

# Proje
Adı: {project.name}
Şirketin sektörü: {sectors}
Açıklama: {(project.description or '-')[:2000]}
İsterler (yöneticinin kısa brifi):
{(project.requirements or '-')[:6000]}
Bütçe: {project.budget_try or 'belirtilmedi'} TL · Hedef tarihler: {project.start_date or '-'} – {project.end_date or '-'}

# Önceki turlarda alınan yanıtlar
{history or 'yok'}

# Daha önce sorulan sorular (tekrar sorma)
{asked_before or 'yok'}

# Bu turun yanıtları
{now_qa or 'ilk tur'}
Yanıtlanmadan geçilen sorular: {'; '.join(skipped) or 'yok'}
Yöneticinin ek notu: {(note or 'yok')[:2000]}

# Web araştırması bulguları (yöneticinin onayıyla yapıldı; kaynaklı)
{research or 'yok'}
{pack_block}
# Mevcut tanım belgesi
{json.dumps(d['charter'], ensure_ascii=False)[:6000] if d['charter'] else 'yok'}

Görevin:
1) Tanım belgesini (charter) yeni bilgilerle güncelle. Bilmediğini uydurma; yöneticinin söylemediğini "assumptions" (varsayım)
   ya da "open_questions" olarak yaz. Teslimatların her biri için kabul ölçütü ve doğrulama yöntemi yaz (otomatik test, ölçüm,
   kanıt, kontrol listesi ya da insan onayı). Kullanıcı akışlarını "workflows" altında yaz (ör. "Ziyaretçi turu filtreler → detayı açar → rezervasyon yapar").
2) Olgunluk puanı ver (0-100): belge planlamaya ne kadar hazır? Eksikleri somut yaz (ör. "İade politikası belirsiz").
3) Sıradaki en önemli en fazla {MAX_QUESTIONS} soruyu sor. ÖNCE GENİŞLİK: henüz hiç sorulmamış iskelet konularına ve brifte geçen
   ama hiç konuşulmamış iş alanlarına (ör. raporlar, saha kullanımı, iş güvenliği, eğitim, mevcut veri) öncelik ver; bir konuya
   (tek bir hesaplama ya da süreç dahil) bir turda en fazla 2 soru ayır ve aynı ayrıntıya üçüncü kez dalma. İş kuralları (ne sunuluyor,
   kontenjan/kapasite, fiyat ve ödeme, kimler yararlanabilir, yerleştirme/onay kuralları) bu konulardan biridir ve ilk iki turda
   mutlaka sorulur. Sonra sektöre özgü ve sık atlanan konular. Her sorunun neden önemli olduğunu bir cümleyle yaz. Belge yeterince olgunsa (puan 85+) soru sorma.
   "Daha önce sorulan sorular" listesindeki bir soruyu aynı ya da benzer biçimde TEKRAR SORMA; yönetici "henüz netleştirmedik"
   dediyse onu varsayım (assumptions) ya da açık soru (open_questions) olarak belgeye yaz ve başka bir konuya geç.
4) "Bunu düşündünüz mü?" türünden en fazla 3 kısa hatırlatma yaz (sık atlanan gereksinimler, gerçekçi olmayan süre/bütçe uyarısı).
5) Web'de araştırılması belgeyi belirgin biçimde güçlendirecek en fazla 2 konu öner (ör. güncel mevzuat, sektördeki benzer çözümler,
   tipik teslimatlar). Araştırmayı sen başlatmazsın; yönetici onaylarsa yapılır. Gerek yoksa boş bırak. Konu metninde kişi/şirket adı olmasın.

Sadece şu JSON'u döndür:
{{"charter": {{"goal": "amaç", "success_criteria": ["ölçülebilir başarı ölçütü"], "stakeholders": ["paydaş"], "users_roles": ["kullanıcı/rol"],
  "scope_in": ["kapsam içi"], "scope_out": ["kapsam dışı"], "constraints": ["kısıt"],
  "deliverables": [{{"name": "teslimat", "acceptance": "kabul ölçütü", "verification": "doğrulama yöntemi"}}],
  "workflows": ["kullanıcı akışı"], "risks": ["risk"], "assumptions": ["varsayım"], "open_questions": ["açık soru"]}},
 "maturity": {{"score": 0, "missing": ["eksik"]}},
 "questions": [{{"topic": "Kapsam", "text": "soru", "why": "neden önemli"}}],
 "reminders": ["Bunu düşündünüz mü: …"], "research_suggestions": ["web'de araştırılacak konu"]}}"""
    from app.services import llm_json  # bozuk/yarım JSON'da bir kez onarım ister (canlı test 16.11)

    try:
        out, result = await llm_json.chat_json(LLMContext(tenant_id=project.tenant_id, purpose="BRAIN", project_id=project.id),
                                               [{"role": "user", "content": prompt}], temperature=0.3, max_tokens=5000, timeout=300)
        charter = _clean_charter(out.get("charter") or {})
        mat = out.get("maturity") or {}
        score = max(0, min(100, int(mat.get("score") or 0)))
        questions = [{"id": f"q{len(d['rounds']) + 1}_{i}", "topic": str(q.get("topic") or "")[:60], "text": str(q.get("text") or "")[:600],
                      "why": str(q.get("why") or "")[:300]} for i, q in enumerate((out.get("questions") or [])[:MAX_QUESTIONS], 1) if q.get("text")]
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Beyin AI geçerli bir yanıt üretemedi; lütfen tekrar deneyin.") from exc
    d["rounds"].append({"at": psvc.now().isoformat(), "qa": qa, "note": (note or "")[:2000] or None, "score": score,
                        "model_code": result.public_model, "credits": float(result.credits or 0)})
    d.update(charter=charter, maturity={"score": score, "missing": [str(m)[:300] for m in (mat.get("missing") or [])][:15]},
             pending=questions, reminders=[str(r)[:400] for r in (out.get("reminders") or [])][:3],
             research_suggestions=[str(r)[:200] for r in (out.get("research_suggestions") or []) if str(r).strip()][:2],
             status="IN_PROGRESS", approved_at=None, approved_by=None, approve_reason=None)
    _save(project, d)
    if project.status == "DRAFT":
        project.status = "PLANNING"
    from app.services import task_flow

    await task_flow.log(db, project, None, "DISCOVERY_ROUND", None, f"Keşif turu {len(d['rounds'])}: olgunluk %{score}, {len(questions)} yeni soru",
                        {"score": score, "answered": sum(1 for x in qa if x["answer"])})
    await db.commit()
    return d


async def approve(db: AsyncSession, project: Project, actor_id, reason: Optional[str] = None) -> Dict[str, Any]:
    from app.services import task_flow

    _editable(project)
    d = state(project)
    if not d["charter"]:
        raise HTTPException(status_code=409, detail="Onaylanacak tanım belgesi yok; önce keşif görüşmesini başlatın.")
    score = d["maturity"]["score"]
    if score < THRESHOLD and not (reason or "").strip():
        raise HTTPException(status_code=422, detail=f"Tanım belgesinin olgunluğu %{score} (eşik %{THRESHOLD}). Eksiklere rağmen onaylamak için gerekçe yazın.")
    d.update(status="APPROVED", approved_at=psvc.now().isoformat(), approved_by=str(actor_id), approve_reason=(reason or "").strip() or None)
    _save(project, d)
    await task_flow.log(db, project, None, "CHARTER_APPROVED", actor_id,
                        f"Proje Tanım Belgesi onaylandı (olgunluk %{score})" + (f"; gerekçe: {reason.strip()}" if (reason or "").strip() else ""),
                        {"score": score, "below_threshold": score < THRESHOLD})
    await db.commit()
    from app.services import brain_learning  # #753: sorulan sorular ve yanıtlanıp belgeye girenler öğrenme kaydına

    await brain_learning.on_charter_approved(project, actor_id, d, THRESHOLD)
    return d


async def skip(db: AsyncSession, project: Project, actor_id, reason: str) -> Dict[str, Any]:
    from app.services import task_flow

    _editable(project)
    if not (reason or "").strip():
        raise HTTPException(status_code=422, detail="Keşfi atlamak için gerekçe yazın; karar kayda geçer.")
    d = state(project)
    d.update(status="SKIPPED", skipped_reason=reason.strip()[:1000], approved_at=None)
    _save(project, d)
    await task_flow.log(db, project, None, "DISCOVERY_SKIPPED", actor_id, f"Keşif atlandı: {reason.strip()[:500]}")
    await db.commit()
    return d


def uuid_of(v) -> uuid.UUID:
    return v if isinstance(v, uuid.UUID) else uuid.UUID(str(v))
