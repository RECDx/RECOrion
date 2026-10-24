"""Edge Connector bağlayıcısı (ADIM 10.5): müşterinin kendi sunucusundaki sistemler (Logo, Mikro vb.).

- Müşteri sunucusunda RECOrion Edge ajanı çalışır (edge_agent/); yalnızca DIŞA bağlanır (müşteri ağına port açılmaz):
  RECOrion'a yoklama yapar, kuyruktaki işi alır, sonucu geri gönderir (app/services/edge.py, /api/v1/edge/*).
- Ajan yalnızca kendi yapılandırma dosyasındaki İZİNLİ SORGU ŞABLONLARINI çalıştırır; SQL müşteri sunucusunda durur.
  RECOrion'a yalnızca şablon kataloğu (ad, açıklama, parametreler, tür) bildirilir; buradan SQL gönderilemez.
- Araçlar bu katalogdan oluşur. Yazma şablonları insan onayına düşer (ADIM 10.1) ve ajan tarafında da varsayılan kapalıdır.
"""
import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.integrations.base import READ, WRITE, Connector, Context, Tool, ToolError

OFFLINE_AFTER = timedelta(seconds=90)  # ajan bu süredir yoklama yapmadıysa çevrimdışı
JOB_WAIT_SECONDS = 25  # araç çağrısı ajanın sonucunu en fazla bu kadar bekler (geçit sınırı 30 sn)
TEMPLATE_NAME = re.compile(r"^[a-z][a-z0-9_]{1,59}$")
MAX_TEMPLATES, MAX_PARAMS = 50, 20
TYPES = {"string": "string", "integer": "integer", "number": "number", "date": "string", "boolean": "boolean"}


def online(seen_at) -> bool:
    return bool(seen_at) and datetime.now(timezone.utc) - seen_at < OFFLINE_AFTER


def clean_catalog(templates: Any) -> List[Dict[str, Any]]:
    """Ajanın bildirdiği kataloğu doğrular ve sadeleştirir (SQL veya bilinmeyen alan saklanmaz)."""
    out = []
    for t in (templates if isinstance(templates, list) else [])[:MAX_TEMPLATES]:
        if not isinstance(t, dict) or not TEMPLATE_NAME.match(str(t.get("name") or "")):
            continue
        params = []
        for p in (t.get("params") if isinstance(t.get("params"), list) else [])[:MAX_PARAMS]:
            if isinstance(p, dict) and TEMPLATE_NAME.match(str(p.get("name") or "")) and p.get("type") in TYPES:
                params.append({"name": p["name"], "type": p["type"], "required": bool(p.get("required", True)),
                               "description": str(p.get("description") or "")[:300],
                               **({"max_length": int(p["max_length"])} if isinstance(p.get("max_length"), int) else {})})
        out.append({"name": t["name"], "description": str(t.get("description") or t["name"])[:500],
                    "kind": WRITE if t.get("kind") == WRITE else READ, "params": params})
    return out


def _schema(params: List[Dict[str, Any]]) -> Dict[str, Any]:
    props = {}
    for p in params:
        prop = {"type": TYPES[p["type"]], "description": p.get("description") or ""}
        if p["type"] == "date":
            prop["format"] = "date"
            prop["description"] = (prop["description"] + " (YYYY-AA-GG)").strip()
        if p.get("max_length"):
            prop["maxLength"] = p["max_length"]
        props[p["name"]] = prop
    return {"type": "object", "properties": props, "required": [p["name"] for p in params if p.get("required")]}


def _runner(template: str):
    async def run(ctx: Context, args: Dict[str, Any]):
        from sqlalchemy import select

        from app.db.models import EdgeJob, IntegrationConnection
        from app.db.session import AsyncSessionLocal

        cid = uuid.UUID(ctx.connection_id)
        async with AsyncSessionLocal() as db:
            conn = await db.get(IntegrationConnection, cid)
            if not conn or not online(conn.agent_seen_at):
                raise ToolError("Edge Connector çevrimdışı: müşteri sunucusundaki RECOrion Edge ajanı çalışmıyor veya bağlanamıyor.")
            job = EdgeJob(tenant_id=conn.tenant_id, connection_id=cid, template=template, params=args or {})
            db.add(job)
            await db.commit()
            job_id = job.id
        deadline = asyncio.get_running_loop().time() + JOB_WAIT_SECONDS
        while asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.5)
            async with AsyncSessionLocal() as db:
                job = (await db.execute(select(EdgeJob).where(EdgeJob.id == job_id))).scalar_one()
                if job.status == "DONE":
                    return job.result
                if job.status == "FAILED":
                    raise ToolError(f"Edge ajanı: {job.error or 'sorgu çalıştırılamadı'}")
        async with AsyncSessionLocal() as db:
            job = await db.get(EdgeJob, job_id)
            if job.status in ("QUEUED", "RUNNING"):
                job.status, job.error, job.done_at = "EXPIRED", "Süre doldu", datetime.now(timezone.utc)
                await db.commit()
        raise ToolError(f"Edge ajanı {JOB_WAIT_SECONDS} sn içinde yanıt vermedi.")
    return run


async def _tools(ctx: Context) -> List[Tool]:
    catalog = clean_catalog((ctx.state.get("agent") or {}).get("templates"))
    return [Tool(t["name"], t["description"], _schema(t["params"]), t["kind"], _runner(t["name"])) for t in catalog]


async def _test(ctx: Context) -> str:
    agent = ctx.state.get("agent") or {}
    if not ctx.state.get("seen_at"):
        raise ToolError("Ajan henüz bağlanmadı. Ajan anahtarı oluşturup müşteri sunucusunda ajanı başlatın.")
    if not online(ctx.state["seen_at"]):
        raise ToolError("Ajan çevrimdışı (son yoklama 90 sn'den eski).")
    n = len(clean_catalog(agent.get("templates")))
    return f"Ajan çevrimiçi · {agent.get('hostname') or 'sunucu'} · sürüm {agent.get('version') or '?'} · {n} izinli şablon"


CONNECTOR = Connector(
    code="edge", title="Edge Connector (şirket sunucusu)",
    description="Şirket sunucusundaki Logo, Mikro gibi sistemlere, orada çalışan RECOrion Edge ajanıyla bağlanır. Ajan yalnızca "
                "dışa bağlanır ve yalnızca sizin tanımladığınız sorgu şablonlarını çalıştırır.",
    tools_fn=_tools,
    test_fn=_test,
)
