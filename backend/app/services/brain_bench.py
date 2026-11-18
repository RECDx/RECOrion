"""
İSTEK #754 — Beyin AI deneme seti (sektörler arası kısa brifler, puanlama, her geliştirmeden sonra yeniden koşma).

Her brif "RECOrion Canlı Test A.Ş." şirketinde bir projeye dönüşür ve yalnız keşif → tanım belgesi → plan önerisi aşaması
koşturulur (adımlar yürütülmez). Yönetici rolünü RECAi oynar: Beyin AI'nın sorularını yalnız gizli cevap anahtarındaki
bilgilerle yanıtlar, sorulmayanı söylemez; böylece "yöneticinin düşünmediğini sordu mu" ölçülür. Proje sonunda gerekçeyle
iptal edilir; deneme projeleri öğrenme kaydı üretmez (brain_learning.capture).

Puan (brif başına 100): Keşif 30 (cevap anahtarı maddelerinin soruyla ortaya çıkan ya da tanım belgesine giren oranı),
Tanım 20 (belgenin bölümleri + olgunluk), Plan yapısı 25 (teslimat/akış bazlı kurgu, yazılımda arayüz tasarımı ve kabul
testi adımı, insan adımı), Doğrulama 25 (adımların somut teslimat/doğrulaması + cevap anahtarının planda karşılanması).
Tüm LLM çağrıları llm_gateway üzerinden (yedek model açık).

Komut satırı (her geliştirmeden sonra):  python -m app.services.brain_bench [kod ...]
"""
import asyncio
import json
import logging
import re
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, BrainBenchRun, Project, Tenant
from app.db.session import AsyncSessionLocal
from app.services import llm_json
from app.services import projects as psvc
from app.services.llm_gateway import LLMContext

logger = logging.getLogger("recorion.brain_bench")

TEST_TENANT_SLUG = "recorion_canli_test"
PROJECT_PREFIX = "Beyin Deneme · "
ROUNDS = 3  # keşif turu (ilk tur + 2 yanıtlı tur)
STALE = timedelta(hours=4)  # bu süreyi aşan RUNNING koşu yarıda kalmış sayılır (ör. sunucu yeniden başladı)
WEIGHTS = {"discovery": 30, "charter": 20, "plan": 25, "verification": 25}
SEED = Path(__file__).resolve().parent.parent / "seed" / "brain_bench.json"
UI_RE = re.compile(r"arayüz|kullanım tasarım|ekran tasarım|ux|ui\b|menü", re.I)
ACCEPT_RE = re.compile(r"kabul test|kullanıcı kabul|uat", re.I)
LAYER_RE = re.compile(r"^(backend|frontend|veritaban\w*|api|test|altyapı|database)(\s+(geliştirme\w*|kurulum\w*))?$", re.I)
_tasks: Set[asyncio.Task] = set()


def cases() -> List[Dict[str, Any]]:
    return json.loads(SEED.read_text(encoding="utf-8"))["cases"]


def _case(code: str) -> Dict[str, Any]:
    for c in cases():
        if c["code"] == code:
            return c
    raise HTTPException(status_code=404, detail=f"Deneme brifi bulunamadı: {code}")


# ---------------------------------------------------------------- RECAi yönetici ve değerlendirici
def _key_text(case: Dict[str, Any]) -> str:
    return "\n".join(f"- {k['id']} [{k['topic']}] {k['fact']}" for k in case["key"])


async def manager_answers(ctx: LLMContext, case: Dict[str, Any], questions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], Set[str], float]:
    """Yönetici rolündeki RECAi: yalnız cevap anahtarından, yalnız sorulana yanıt verir. (yanıtlar, ortaya çıkan maddeler, kredi)"""
    if not questions:
        return [], set(), 0.0
    qs = "\n".join(f"- {q['id']}: {q['text']}" for q in questions)
    prompt = f"""Bir proje yöneticisini canlandırıyorsun. Projen: "{case['title']}". Brifin: "{case['brief']}"
Aşağıda yalnız senin bildiğin gerçekler var (cevap anahtarı). Beyin AI sana sorular soruyor.
Kurallar:
- Her soruya YALNIZ o soruyla doğrudan ilgili gerçeklerle, kısa ve doğal bir yöneticinin dilinde yanıt ver.
- Sorulmayan konuyu söyleme; ilgili gerçek yoksa "Bunu henüz netleştirmedik." de. Gerçek uydurma.
- Her yanıtta kullandığın gerçeklerin kimliklerini "facts" içine yaz (yoksa boş liste).

# Bildiğin gerçekler
{_key_text(case)}

# Sorular
{qs}

Sadece şu JSON'u döndür: {{"answers": [{{"id": "soru kimliği", "answer": "yanıt", "facts": ["k1"]}}]}}"""
    out, result = await llm_json.chat_json(ctx, [{"role": "user", "content": prompt}], temperature=0.2, max_tokens=2000, timeout=240)
    ids = {q["id"] for q in questions}
    valid = {k["id"] for k in case["key"]}
    answers, revealed = [], set()
    for a in out.get("answers") or []:
        if a.get("id") in ids:
            answers.append({"id": a["id"], "answer": str(a.get("answer") or "")[:1500]})
            revealed |= {str(f) for f in (a.get("facts") or []) if str(f) in valid}
    return answers, revealed, float(result.credits or 0)


async def judge(ctx: LLMContext, case: Dict[str, Any], charter: Dict[str, Any], plan: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
    steps = [{k: s.get(k) for k in ("key", "title", "deliverable", "verification", "verification_type", "acceptance_criteria")}
             | {"insan": bool(s.get("assignee_human_id"))} for s in (plan.get("steps") or [])]
    prompt = f"""Bir proje planlama asistanının (Beyin AI) çıktısını değerlendiriyorsun. Tarafsız ve katı ol.
Proje: {case['title']} ({case['sector']}). Brif: "{case['brief']}"

# Cevap anahtarı (iyi bir keşfin ortaya çıkarması gereken gerçekler)
{_key_text(case)}

# Onaylanan Proje Tanım Belgesi
{json.dumps(charter, ensure_ascii=False)[:7000]}

# Önerilen plan adımları
{json.dumps(steps, ensure_ascii=False)[:7000]}

Değerlendir:
1) in_charter: tanım belgesinde karşılığı (aynı anlamda) bulunan cevap anahtarı maddeleri.
2) in_plan: planda bir adım, teslimat ya da doğrulamayla karşılanan maddeler.
3) structure (0-10): plan teknik katmanlara (Backend/Frontend/Test) göre değil teslimatlara ve kullanıcı akışlarına göre mi
   kurulu, adımlar uçtan uca bir sonuç veriyor mu, sıra ve bağımlılıklar mantıklı mı.
4) note: en önemli 1-3 eksik, kısa.
Sadece şu JSON'u döndür: {{"in_charter": ["k1"], "in_plan": ["k2"], "structure": 7, "note": "kısa gerekçe"}}"""
    out, result = await llm_json.chat_json(ctx, [{"role": "user", "content": prompt}], temperature=0.0, max_tokens=1500, timeout=240)
    valid = {k["id"] for k in case["key"]}
    try:
        structure = max(0, min(10, int(out.get("structure") or 0)))
    except (TypeError, ValueError):
        structure = 0
    return ({"in_charter": sorted({str(x) for x in out.get("in_charter") or []} & valid),
             "in_plan": sorted({str(x) for x in out.get("in_plan") or []} & valid),
             "structure": structure, "note": str(out.get("note") or "")[:600]}, float(result.credits or 0))


# ---------------------------------------------------------------- puanlama (kural tabanlı + değerlendirici)
def _specific(text: Optional[str]) -> bool:
    t = (text or "").strip().lower()
    return len(t) >= 25 and not any(g in t for g in ("sayfa açılıyor", "kod var", "tamamlandı", "yapıldı"))


def score(case: Dict[str, Any], revealed: Set[str], d: Dict[str, Any], plan: Dict[str, Any], j: Dict[str, Any]) -> Dict[str, Any]:
    keys = [k["id"] for k in case["key"]]
    n = len(keys) or 1
    found = set(revealed) | set(j.get("in_charter") or [])
    c = d.get("charter") or {}
    parts = {"goal": bool(c.get("goal")), "success_criteria": bool(c.get("success_criteria")), "scope_in": bool(c.get("scope_in")),
             "scope_out": bool(c.get("scope_out")), "users_roles": bool(c.get("users_roles") or c.get("stakeholders")),
             "deliverables": bool(c.get("deliverables")) and all(x.get("acceptance") and x.get("verification") for x in c["deliverables"]),
             "risks": bool(c.get("risks"))}
    if case["expect"].get("software"):
        parts["workflows"] = bool(c.get("workflows"))
    maturity = int((d.get("maturity") or {}).get("score") or 0)
    steps = plan.get("steps") or []
    titles = [s.get("title") or "" for s in steps]
    checks: Dict[str, bool] = {}
    if case["expect"].get("software"):
        checks["ui_step"] = any(UI_RE.search(t) for t in titles)
        checks["acceptance_step"] = any(ACCEPT_RE.search(t) for t in titles)
    if case["expect"].get("human"):
        checks["human_step"] = any(s.get("assignee_human_id") for s in steps) or any(
            "insan" in (s.get("job_title") or "").lower() for s in steps)
    layered = sum(1 for t in titles if LAYER_RE.match(t.strip()))
    checks["not_layered"] = layered <= max(1, len(titles) // 5)
    verified = sum(1 for s in steps if s.get("deliverable") and _specific(s.get("verification")))
    in_plan = set(j.get("in_plan") or [])
    s_disc = WEIGHTS["discovery"] * len(found & set(keys)) / n
    s_charter = 12 * sum(parts.values()) / len(parts) + 8 * maturity / 100
    s_plan = 15 * (j.get("structure") or 0) / 10 + 10 * (sum(checks.values()) / len(checks) if checks else 1)
    s_verif = (10 * verified / len(steps) if steps else 0) + 15 * len(in_plan & set(keys)) / n
    scores = {"discovery": round(s_disc, 1), "charter": round(s_charter, 1), "plan": round(s_plan, 1), "verification": round(s_verif, 1)}
    scores["total"] = round(sum(scores.values()), 1)
    missed = [k for k in case["key"] if k["id"] not in found]
    return {"scores": scores, "details": {
        "found": sorted(found), "revealed": sorted(revealed), "missed": [f"[{k['topic']}] {k['fact']}" for k in missed],
        "charter_parts": parts, "maturity": maturity, "plan_checks": checks, "layered_steps": layered,
        "steps": len(steps), "verified_steps": verified, "in_plan": sorted(in_plan), "structure": j.get("structure"),
        "judge_note": j.get("note"), "step_titles": titles[:40]}}


# ---------------------------------------------------------------- koşturma
async def _test_tenant(db: AsyncSession) -> Tuple[Tenant, Actor]:
    tenant = (await db.execute(select(Tenant).where(Tenant.slug == TEST_TENANT_SLUG))).scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=409, detail="Canlı test şirketi bulunamadı; deneme seti yalnız orada koşar.")
    manager = (await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.actor_type == "HUMAN", Actor.status != "DISABLED")
                                .order_by(Actor.created_at).limit(1))).scalar_one_or_none()
    if not manager:
        raise HTTPException(status_code=409, detail="Canlı test şirketinde proje yöneticisi olacak insan kullanıcı yok.")
    return tenant, manager


async def run_case(case: Dict[str, Any]) -> Dict[str, Any]:
    from app.services import discovery, project_planning

    t0 = time.monotonic()
    out: Dict[str, Any] = {"code": case["code"], "title": case["title"], "sector": case["sector"], "credits": 0.0}
    async with AsyncSessionLocal() as db:
        tenant, manager = await _test_tenant(db)
        name = f"{PROJECT_PREFIX}{case['title']}"
        project = Project(tenant_id=tenant.id, slug=await psvc.unique_slug(db, tenant.id, name), name=name, requirements=case["brief"],
                          field_package="YAZILIM" if case["expect"].get("software") else "GENEL", status="DRAFT",
                          manager_actor_id=manager.id, created_by_actor_id=manager.id, settings={"brain_bench": case["code"]})
        db.add(project)
        await db.commit()
        out["project_id"] = str(project.id)
        ctx = LLMContext(tenant_id=tenant.id, purpose="BRAIN", project_id=project.id)
        revealed: Set[str] = set()
        stage = "keşif"
        try:
            d = await discovery.run_round(db, project, [])
            for _ in range(ROUNDS - 1):
                if not d.get("pending"):
                    break
                answers, got, cr = await manager_answers(ctx, case, d["pending"])
                revealed |= got
                out["credits"] += cr
                d = await discovery.run_round(db, project, answers)
            out["credits"] += sum(float(r.get("credits") or 0) for r in d["rounds"])
            out["rounds"] = len(d["rounds"])
            out["discovery_s"] = round(time.monotonic() - t0)
            d = await discovery.approve(db, project, manager.id, "Beyin deneme seti: keşif turu sınırı" if d["maturity"]["score"] < discovery.THRESHOLD else None)
            stage = "plan"
            t1 = time.monotonic()
            plan = await project_planning.suggest_plan(db, project)
            out["plan_s"] = round(time.monotonic() - t1)
            stage = "değerlendirme"
            j, cr = await judge(ctx, case, d["charter"], plan)
            out["credits"] += cr
            out.update(score(case, revealed, d, plan, j))
            out["charter"] = d["charter"]
        except HTTPException as exc:
            out["error"] = f"{stage}: {exc.detail}"
        except Exception as exc:  # EVREN yanıtsız, bozuk JSON vb. — koşu sürer, brif kalır
            logger.exception("Beyin deneme brifi %s kaldı", case["code"])
            out["error"] = f"{stage}: {type(exc).__name__}: {str(exc)[:300]}"
        finally:
            try:
                await db.refresh(project)
                if project.status not in ("COMPLETED", "CANCELLED"):
                    await psvc.transition(db, project, "cancel", "Beyin deneme seti: yalnız keşif, tanım ve plan ölçüldü")
            except Exception:
                await db.rollback()
                logger.exception("Deneme projesi kapatılamadı")
        out["credits"] = round(out["credits"], 2)
        out["seconds"] = round(time.monotonic() - t0)
    return out


async def execute(run_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        run = await db.get(BrainBenchRun, run_id)
        codes = list(run.case_codes or [])
    results: List[Dict[str, Any]] = []
    try:
        for code in codes:
            results.append(await run_case(_case(code)))
            async with AsyncSessionLocal() as db:  # ilerleme ekranda görünsün
                run = await db.get(BrainBenchRun, run_id)
                run.results = list(results)
                await db.commit()
        ok = [r["scores"]["total"] for r in results if r.get("scores")]
        async with AsyncSessionLocal() as db:
            run = await db.get(BrainBenchRun, run_id)
            run.status = "DONE" if ok else "FAILED"
            run.total = round(sum(ok) / len(ok), 1) if ok else None
            run.error = None if ok else "Hiçbir brif puanlanamadı (EVREN yanıtsız olabilir)."
            run.finished_at = psvc.now()
            await db.commit()
    except Exception as exc:
        logger.exception("Beyin deneme seti koşusu kaldı")
        async with AsyncSessionLocal() as db:
            run = await db.get(BrainBenchRun, run_id)
            run.status, run.error, run.finished_at = "FAILED", f"{type(exc).__name__}: {str(exc)[:500]}", psvc.now()
            await db.commit()


async def expire_stale(db: AsyncSession) -> None:
    cutoff = psvc.now() - STALE
    for r in (await db.execute(select(BrainBenchRun).where(BrainBenchRun.status == "RUNNING", BrainBenchRun.started_at < cutoff))).scalars():
        r.status, r.finished_at = "FAILED", psvc.now()
        r.error = "Koşu yarıda kaldı (sunucu yeniden başlamış olabilir)."
    await db.commit()


async def create_run(db: AsyncSession, codes: Optional[List[str]], label: Optional[str], started_by=None) -> BrainBenchRun:
    await expire_stale(db)
    if (await db.execute(select(BrainBenchRun.id).where(BrainBenchRun.status == "RUNNING"))).first():
        raise HTTPException(status_code=409, detail="Bir deneme seti koşusu zaten sürüyor; bitmesini bekleyin.")
    all_codes = [c["code"] for c in cases()]
    codes = [c for c in (codes or all_codes) if c in all_codes]
    if not codes:
        raise HTTPException(status_code=422, detail="Koşturulacak brif seçin.")
    await _test_tenant(db)
    run = BrainBenchRun(status="RUNNING", label=(label or "").strip()[:200] or None, case_codes=codes, results=[],
                        started_by=started_by, started_at=psvc.now())
    db.add(run)
    await db.commit()
    return run


def spawn(run_id: uuid.UUID) -> None:
    t = asyncio.get_running_loop().create_task(execute(run_id))
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)


def compare(run: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Önceki tamamlanmış koşuyla brif başına fark."""
    prev = {r["code"]: r for r in (previous or {}).get("results") or [] if r.get("scores")}
    out = {}
    for r in run.get("results") or []:
        p = prev.get(r["code"])
        if r.get("scores") and p:
            out[r["code"]] = {k: round(r["scores"][k] - p["scores"][k], 1) for k in r["scores"]}
    return out


def out(run: BrainBenchRun) -> Dict[str, Any]:
    return {"id": str(run.id), "status": run.status, "label": run.label, "case_codes": run.case_codes or [], "results": run.results or [],
            "total": float(run.total) if run.total is not None else None, "error": run.error,
            "started_at": run.started_at, "finished_at": run.finished_at}


async def _cli(codes: List[str]) -> None:
    async with AsyncSessionLocal() as db:
        run = await create_run(db, codes or None, "komut satırı")
        rid = run.id
    await execute(rid)
    async with AsyncSessionLocal() as db:
        run = out(await db.get(BrainBenchRun, rid))
    print(f"Koşu {rid}: {run['status']} · ortalama {run['total']}")
    for r in run["results"]:
        s = r.get("scores")
        print(f"- {r['code']:<14} " + (f"{s['total']:>5} (keşif {s['discovery']}, tanım {s['charter']}, plan {s['plan']}, doğrulama {s['verification']})"
                                       if s else f"KALDI: {r.get('error')}") + f" · {r.get('seconds')} sn · {r.get('credits')} kredi")


if __name__ == "__main__":
    asyncio.run(_cli(sys.argv[1:]))
