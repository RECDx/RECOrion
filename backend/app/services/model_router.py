"""
Akıllı model yönlendirici ve kalite test seti (ADIM 11.4; kullanıcı kararı 24.10.2026: ölçüme dayalı öneri + onaylı geçiş).

- İş türü (CODE, ANALYSIS, SUMMARY, WRITING, STRUCTURED) adım/sohbet metninden ve AI personelin unvanından sınıflandırılır.
- Kalite test seti (app/seed/quality_suite.json) seçilen modellerde koşar; her çıktı KURALLA puanlanır (JSON geçerliliği ve
  alanları, kod sözdizimi — kod asla çalıştırılmaz —, kelime/madde sınırı, zorunlu/yasak ifadeler): tekrarlanabilir, LLM hakemi yok.
- Öneri: kalite (0.6) + koşudaki hız (0.2) + son 7 günün gerçek güvenilirliği (0.2); kalite eşiğinin altı önerilmez.
- Onay: Süper Admin onaylayınca 'model.route.<İŞ_TÜRÜ>' platform varsayılanı olur (iz: model_route_decisions). AI personelin
  elle seçilmiş modeli ve açık model seçimi her zaman önce gelir; meşgul modelde yedek model mekanizması aynen sürer.
"""
import ast
import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LLMCall, LLMModel, ModelRouteDecision, QualityResult, QualityRun, SystemSetting
from app.db.session import AsyncSessionLocal

logger = logging.getLogger("recorion.router")

SUITE_FILE = Path(__file__).resolve().parent.parent / "seed" / "quality_suite.json"
TASK_TYPES = {"CODE": "Kod yazma", "ANALYSIS": "Analiz ve planlama", "SUMMARY": "Özetleme", "WRITING": "Türkçe yazım",
              "STRUCTURED": "Yapılandırılmış çıktı (JSON)"}
ROUTE_KEY = "model.route.{}"
QUALITY_MIN = 0.7
WEIGHTS = {"quality": 0.6, "speed": 0.2, "reliability": 0.2}
LIVE_DAYS, LIVE_MIN_CALLS = 7, 20
TEST_PURPOSE = "QUALITY_TEST"
_tasks: set = set()

_KEYWORDS = {
    "CODE": ["kod", "yazılım", "geliştir", "api", "backend", "frontend", "veritaban", "sql", "script", "betik", "python", "javascript",
             "refactor", "birim test", "hata düzelt", "entegrasyon geliştir", "uygulama geliştir"],
    "SUMMARY": ["özet", "özetle", "tutanak", "toplantı not", "kısalt", "rapor özeti"],
    "WRITING": ["metin", "yazı", "e-posta", "eposta", "duyuru", "içerik", "makale", "blog", "basın bülten", "sosyal medya", "dilekçe",
                "mektup", "sözleşme metni", "yazım", "çeviri"],
    "STRUCTURED": ["json", "tablo", "sınıflandır", "veri çıkar", "alanları çıkar", "eşleştirme tablosu", "csv", "form doldur"],
}
_TITLE_HINTS = {"geliştirici": "CODE", "developer": "CODE", "yazılım": "CODE", "editör": "WRITING", "içerik": "WRITING",
                "metin yazar": "WRITING", "çevirmen": "WRITING"}


def _norm(t: str) -> str:
    return (t or "").replace("I", "ı").replace("İ", "i").lower()


def classify(*texts: str, job_title: Optional[str] = None) -> str:
    """İş türü: anahtar kelime sayımı + unvan ipucu; belirsizse ANALYSIS."""
    text = _norm(" ".join(t for t in texts if t))
    scores = {tt: sum(text.count(k) for k in kws) for tt, kws in _KEYWORDS.items()}
    title = _norm(job_title or "")
    for hint, tt in _TITLE_HINTS.items():
        if hint in title:
            scores[tt] = scores.get(tt, 0) + 2
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0] if best[1] > 0 else "ANALYSIS"


# ---------------------------------------------------------------- kurala dayalı puanlama
def _json(text: str) -> Any:
    t = (text or "").strip()
    if "```" in t:
        t = t.split("```")[1].removeprefix("json").strip()
    start = min([i for i in (t.find("{"), t.find("[")) if i >= 0], default=-1)
    if start < 0:
        raise ValueError("JSON yok")
    end = max(t.rfind("}"), t.rfind("]"))
    return json.loads(t[start:end + 1])


def _python(text: str) -> str:
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text or "", re.S)
    return m.group(1) if m else (text or "")


def _words(text: str) -> int:
    return len(re.findall(r"\w+", text or ""))


def _list_items(text: str) -> int:
    return len(re.findall(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+\S", text or ""))


def _check(c: Dict[str, Any], out: str) -> bool:
    t, v = c["type"], c.get("value")
    try:
        if t == "contains_any":
            return any(x.lower() in out.lower() for x in v)
        if t == "contains_all":
            return all(x.lower() in out.lower() for x in v)
        if t == "not_contains":
            return not any(x.lower() in out.lower() for x in v)
        if t == "regex":
            return re.search(v, out) is not None
        if t == "count_regex":
            return len(re.findall(v, out)) >= c.get("min", 1)
        if t == "max_words":
            return _words(out) <= v
        if t == "min_list_items":
            return _list_items(out) >= v
        if t == "list_items_between":
            return v[0] <= _list_items(out) <= v[1]
        if t == "turkish":
            return re.search("[çğıöşüÇĞİÖŞÜ]", out) is not None
        if t == "python_parse":
            ast.parse(_python(out))
            return True
        if t == "python_defines":
            return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == v for n in ast.walk(ast.parse(_python(out))))
        if t == "json_valid":
            _json(out)
            return True
        if t == "json_keys":
            d = _json(out)
            return isinstance(d, dict) and all(k in d for k in v)
        if t == "json_equals":
            return str(_json(out).get(c["path"])).strip() == str(v)
        if t == "json_number":
            raw = _json(out).get(c["path"])
            num = float(str(raw).replace(".", "").replace(",", ".")) if isinstance(raw, str) else float(raw)
            return abs(num - float(v)) < 0.01
        if t == "json_list_map":
            d = _json(out)
            got = {str(x.get(c["key"])): str(x.get(c["field"])).upper() for x in d if isinstance(x, dict)}
            return all(got.get(k) == val for k, val in v.items())
        if t == "json_list_min":
            items = _json(out).get(c["path"])
            return isinstance(items, list) and len(items) >= v
        if t == "json_items_keys":
            items = _json(out).get(c["path"])
            return isinstance(items, list) and bool(items) and all(isinstance(x, dict) and all(k in x for k in v) for x in items)
        if t == "json_bool":
            return _json(out).get(c["path"]) is v
        if t == "json_in":
            return str(_json(out).get(c["path"])).upper() in [str(x).upper() for x in v]
        if t == "json_contains":  # alan (metin/liste) içinde ifade geçer
            return v.lower() in json.dumps(_json(out).get(c["path"]), ensure_ascii=False).lower()
        if t == "json_deps_valid":  # adım bağımlılıkları var olan anahtarlara işaret eder, kendine bağlı değil
            steps = _json(out).get(c["path"]) or []
            keys = {str(s.get("key")) for s in steps}
            return bool(steps) and all(str(d) in keys and str(d) != str(s.get("key")) for s in steps for d in (s.get("depends_on") or []))
    except (ValueError, SyntaxError, TypeError, AttributeError, json.JSONDecodeError):
        return False
    return False


def grade(case: Dict[str, Any], output: str) -> Tuple[float, List[Dict[str, Any]]]:
    results = [{"type": c["type"], "ok": _check(c, output or ""), "weight": c.get("weight", 1)} for c in case["checks"]]
    total = sum(r["weight"] for r in results) or 1
    return round(sum(r["weight"] for r in results if r["ok"]) / total, 3), results


def load_suite() -> Dict[str, Any]:
    return json.loads(SUITE_FILE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- koşu
async def _set_run(run_id: uuid.UUID, **values) -> None:
    async with AsyncSessionLocal() as db:
        run = await db.get(QualityRun, run_id)
        for k, v in values.items():
            setattr(run, k, v)
        await db.commit()


async def _run_case(run_id: uuid.UUID, model_code: str, case: Dict[str, Any]) -> None:
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext

    started = time.monotonic()
    out, err, tin, tout = "", None, None, None
    try:
        r = await llm_gateway.chat(LLMContext(tenant_id=None, purpose=TEST_PURPOSE), [{"role": "user", "content": case["prompt"]}],
                                   model_code=model_code, temperature=0.1, max_tokens=case.get("max_tokens", 800), timeout=180)
        out, tin, tout = r.content or "", r.tokens_in, r.tokens_out
    except Exception as exc:  # modelin hatası puana yansır (0), koşu sürer
        err = str(exc)[:500]
    score, checks = grade(case, out) if not err else (0.0, [])
    async with AsyncSessionLocal() as db:
        db.add(QualityResult(run_id=run_id, model_code=model_code, case_code=case["code"], task_type=case["task_type"], score=score,
                             checks=checks, latency_ms=int((time.monotonic() - started) * 1000), tokens_in=tin, tokens_out=tout,
                             output_excerpt=out[:1500], error=err))
        await db.commit()


async def run_suite(run_id: uuid.UUID, models: List[str]) -> None:
    suite = load_suite()
    total, done = len(models) * len(suite["cases"]), 0
    sem = asyncio.Semaphore(3)  # EVREN'i boğmamak için aynı anda en fazla 3 çağrı

    async def one(model_code: str, case: Dict[str, Any]) -> None:
        nonlocal done
        async with sem:
            await _run_case(run_id, model_code, case)
        done += 1
        await _set_run(run_id, progress=f"{done}/{total} vaka")
    try:
        await asyncio.gather(*(one(m, c) for m in models for c in suite["cases"]))
        await _set_run(run_id, status="DONE", finished_at=datetime.now(timezone.utc), progress=f"{total}/{total} vaka")
    except Exception as exc:
        logger.exception("Kalite koşusu başarısız (%s)", run_id)
        await _set_run(run_id, status="FAILED", error=f"{exc.__class__.__name__}", finished_at=datetime.now(timezone.utc))


def start(run_id: uuid.UUID, models: List[str]) -> None:
    task = asyncio.get_running_loop().create_task(run_suite(run_id, models))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


# ---------------------------------------------------------------- ölçümler, öneri, onay
async def live_metrics(db: AsyncSession, days: int = LIVE_DAYS) -> Dict[str, Dict[str, Any]]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (await db.execute(select(
        LLMCall.model_code, func.count(), func.count().filter(LLMCall.status != "SUCCESS"),
        func.percentile_cont(0.5).within_group(LLMCall.latency_ms))
        .where(LLMCall.created_at >= since, LLMCall.purpose.notin_((TEST_PURPOSE, "EMBEDDING", "RERANK", "OCR", "GUARD", "TRANSCRIPTION")))
        .group_by(LLMCall.model_code))).all()
    return {m: {"calls": n, "error_rate": round(e / n, 3) if n else None, "p50_ms": int(p) if p is not None else None} for m, n, e, p in rows}


async def current_routes(db: AsyncSession) -> Dict[str, Optional[str]]:
    keys = {ROUTE_KEY.format(tt): tt for tt in TASK_TYPES}
    rows = (await db.execute(select(SystemSetting).where(SystemSetting.key.in_(keys)))).scalars().all()
    got = {keys[r.key]: r.value for r in rows}
    return {tt: got.get(tt) for tt in TASK_TYPES}


async def recommend(db: AsyncSession, run_id: uuid.UUID) -> Dict[str, Any]:
    rows = (await db.execute(select(QualityResult).where(QualityResult.run_id == run_id))).scalars().all()
    live = await live_metrics(db)
    routes = await current_routes(db)
    by: Dict[Tuple[str, str], List[QualityResult]] = {}
    for r in rows:
        by.setdefault((r.task_type, r.model_code), []).append(r)
    out = {}
    for tt in TASK_TYPES:
        cands = []
        lat = {m: sorted(x.latency_ms or 0 for x in rs)[len(rs) // 2] for (t, m), rs in by.items() if t == tt}
        fastest = min(lat.values(), default=0) or 1
        for (t, m), rs in by.items():
            if t != tt:
                continue
            quality = sum(float(x.score) for x in rs) / len(rs)
            speed = min(1.0, fastest / (lat[m] or fastest))
            lv = live.get(m) or {}
            if (lv.get("calls") or 0) >= LIVE_MIN_CALLS and lv.get("error_rate") is not None:
                reliability, rel_src = 1 - lv["error_rate"], "canlı"
            else:
                reliability, rel_src = 1 - sum(1 for x in rs if x.error) / len(rs), "test"
            combined = WEIGHTS["quality"] * quality + WEIGHTS["speed"] * speed + WEIGHTS["reliability"] * reliability
            cands.append({"model_code": m, "quality": round(quality, 3), "speed": round(speed, 3), "reliability": round(reliability, 3),
                          "reliability_source": rel_src, "median_ms": lat[m], "score": round(combined, 3), "eligible": quality >= QUALITY_MIN,
                          "live": lv})
        cands.sort(key=lambda c: (c["eligible"], c["score"]), reverse=True)
        best = cands[0] if cands and cands[0]["eligible"] else None
        out[tt] = {"label": TASK_TYPES[tt], "current": routes.get(tt), "recommended": best["model_code"] if best else None,
                   "candidates": cands}
    return out


async def approve(db: AsyncSession, task_type: str, model_code: Optional[str], actor_id, run_id: Optional[uuid.UUID],
                  note: Optional[str], evidence: Optional[Dict[str, Any]]) -> ModelRouteDecision:
    from fastapi import HTTPException

    if task_type not in TASK_TYPES:
        raise HTTPException(status_code=422, detail="Bilinmeyen iş türü.")
    if model_code:
        m = (await db.execute(select(LLMModel).where(func.lower(LLMModel.model_code) == model_code.lower()))).scalar_one_or_none()
        if not m or m.status != "ACTIVE" or m.model_type != "CHAT":
            raise HTTPException(status_code=422, detail="Bu model etkin bir sohbet modeli değil.")
        model_code = m.model_code
    key = ROUTE_KEY.format(task_type)
    setting = await db.get(SystemSetting, key)
    previous = setting.value if setting else None
    if model_code:
        if setting:
            setting.value = model_code
        else:
            db.add(SystemSetting(key=key, value=model_code, description=f"Model yönlendirici: {TASK_TYPES[task_type]} (Süper Admin onaylı)"))
    elif setting:
        await db.delete(setting)
    d = ModelRouteDecision(task_type=task_type, model_code=model_code, previous_model_code=previous, run_id=run_id, evidence=evidence,
                           note=(note or "").strip() or None, decided_by_actor_id=actor_id)
    db.add(d)
    await db.commit()
    return d
