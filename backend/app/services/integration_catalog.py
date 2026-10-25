"""
Bağlantı kataloğu ve RECAi bağlanma rehberi (ADIM 12.1).

Katalog platform genelidir (RECDx Süper Admin yönetir): her kart bir sistemi ve bağlanma yolunu tanımlar
(NATIVE / MCP_OAUTH / MCP_TOKEN / EDGE / PLANNED). Kart kimlik bilgisi içermez; preset yalnızca düz ayarlardır.
Rehber: şirket yöneticisi "Logo Tiger 3 kullanıyoruz" gibi yazar; RECAi katalogdan uygun kartı ve adımları önerir
(şirketin kredisinden, LLM geçidiyle). Önerilen kart kodu katalogda yoksa yok sayılır (uydurma kart gösterilmez).
"""
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import integrations
from app.db.models import IntegrationCatalogEntry
from app.services import llm_gateway
from app.services.llm_gateway import LLMContext

logger = logging.getLogger("recorion.catalog")
SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "integration_catalog.json"
METHODS = ("NATIVE", "MCP_OAUTH", "MCP_TOKEN", "EDGE", "PLANNED")
CATEGORIES = ("ERP", "CRM", "İş takibi", "Doküman", "Yazılım", "Müşteri destek", "Mesajlaşma", "Finans", "Tasarım", "Diğer")
METHOD_LABEL = {"NATIVE": "Doğrudan bağlantı", "MCP_OAUTH": "Tek tık giriş (MCP)", "MCP_TOKEN": "MCP sunucusu",
                "EDGE": "Şirket sunucusu (Edge)", "PLANNED": "Yakında"}
CODE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


def out(e: IntegrationCatalogEntry) -> Dict[str, Any]:
    return {"id": str(e.id), "code": e.code, "title": e.title, "vendor": e.vendor, "category": e.category, "method": e.method,
            "method_label": METHOD_LABEL.get(e.method, e.method), "connector": e.connector, "preset": e.preset or {},
            "description": e.description, "setup_steps": e.setup_steps or [], "keywords": e.keywords, "sort": e.sort, "status": e.status,
            "requires_app": e.requires_app}


def validate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Süper Admin'in girdiği kartı doğrular; hatada ValueError (anlaşılır ileti)."""
    method = data.get("method")
    if method not in METHODS:
        raise ValueError("Bağlanma yolu geçersiz.")
    if data.get("category") not in CATEGORIES:
        raise ValueError("Kategori geçersiz.")
    connector = data.get("connector") or None
    if method == "PLANNED":
        connector = None
    elif connector not in integrations.REGISTRY:
        raise ValueError("Bağlayıcı geçersiz.")
    if method.startswith("MCP_") and connector != "mcp" or method == "EDGE" and connector != "edge":
        raise ValueError("Bağlanma yolu ile bağlayıcı uyuşmuyor.")
    preset = data.get("preset") or {}
    if not isinstance(preset, dict):
        raise ValueError("Ön ayar bir nesne olmalı.")
    if connector:
        keys = {f.key for f in integrations.get(connector).all_config_fields}
        unknown = set(preset) - keys
        if unknown:
            raise ValueError(f"Ön ayarda bilinmeyen alan: {', '.join(sorted(unknown))}")
    if method == "MCP_OAUTH" and preset.get("auth_mode") != "oauth":
        preset = {**preset, "auth_mode": "oauth"}
    steps = [str(s).strip()[:500] for s in (data.get("setup_steps") or []) if str(s).strip()][:12]
    return {"title": str(data.get("title") or "").strip()[:120], "vendor": (str(data.get("vendor") or "").strip()[:120] or None),
            "category": data["category"], "method": method, "connector": connector, "preset": preset,
            "description": (str(data.get("description") or "").strip()[:2000] or None), "setup_steps": steps,
            "keywords": (str(data.get("keywords") or "").strip()[:500] or None), "sort": int(data.get("sort") or 100),
            "requires_app": data.get("requires_app") if data.get("requires_app") in ("recqmind", "recslip") else None}


async def ensure_catalog(db: AsyncSession, path: Path = SEED_FILE) -> int:
    """Tohum dosyasındaki kartlardan eksik olanları ekler (var olana ve Süper Admin düzenlemesine dokunulmaz)."""
    if not path.exists():
        return 0
    have = set((await db.execute(select(IntegrationCatalogEntry.code))).scalars())
    added = 0
    for raw in json.loads(path.read_text(encoding="utf-8")):
        if raw["code"] in have:
            continue
        db.add(IntegrationCatalogEntry(code=raw["code"], **validate(raw)))
        added += 1
    await db.commit()
    return added


async def active(db: AsyncSession, tenant=None) -> List[IntegrationCatalogEntry]:
    """Etkin kartlar. RECDx uygulama kartları (requires_app) yalnızca o uygulamayı kullanan ve Odoo'su olan şirkete görünür."""
    from app.services import recdx_apps

    rows = list((await db.execute(select(IntegrationCatalogEntry).where(IntegrationCatalogEntry.status == "ACTIVE")
                                  .order_by(IntegrationCatalogEntry.sort, IntegrationCatalogEntry.title))).scalars())
    return [e for e in rows if not e.requires_app or (tenant is not None and recdx_apps.is_active(tenant, e.requires_app))]


ADVISE_PROMPT = """Sen RECAi'sin: RECOrion'da şirketin dış sistemlerini bağlamasına yardım ediyorsun.
Şirket yöneticisi kullandığı sistemi anlattı. Aşağıdaki katalogdan en uygun kartı seç ve nasıl bağlanacağını kısa adımlarla anlat.
Kurallar: Yalnızca katalogdaki kart kodlarını kullan; uygun kart yoksa "code": null ver ve en yakın yolu öner (çoğu zaman
şirket sunucusundaki sistemler için "custom_edge", MCP sunucusu olan servisler için "custom_mcp"). Bilmediğin sürüm, ürün
veya özellik uydurma; emin değilsen "notes" içinde belirt. Kimlik bilgisi (şifre, anahtar) isteme veya yazma.
Yanıtın YALNIZCA şu JSON olsun:
{"code": "katalog kodu veya null", "summary": "1-2 cümle: hangi yolla bağlanılır, neden",
 "steps": ["kısa adım", "..."], "notes": "dikkat edilecekler (yetki, sürüm, ağ) veya boş"}
Katalog:
"""


def _parse(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


async def advise(db: AsyncSession, tenant_id: uuid.UUID, actor_id: Optional[uuid.UUID], text: str) -> Dict[str, Any]:
    entries = await active(db)
    by_code = {e.code: e for e in entries}
    catalog = "\n".join(f"- {e.code}: {e.title} [{e.category}; {METHOD_LABEL.get(e.method)}] {e.description or ''} ({e.keywords or ''})"
                        for e in entries)
    ctx = LLMContext(tenant_id=tenant_id, purpose="BRAIN", actor_id=None, task_type="STRUCTURED")
    messages = [{"role": "system", "content": ADVISE_PROMPT + catalog}, {"role": "user", "content": text.strip()[:1500]}]
    data = None
    for _ in range(2):  # geçersiz JSON'da bir kez daha
        result = await llm_gateway.chat(ctx, messages, temperature=0.2, max_tokens=1500, timeout=120, fallback=True)
        data = _parse(result.content)
        if data:
            break
        messages = messages + [{"role": "assistant", "content": result.content or ""},
                               {"role": "user", "content": "Yalnızca istenen JSON'u ver."}]
    if not data:
        raise ValueError("RECAi şu an öneri üretemedi; biraz sonra yeniden deneyin.")
    entry = by_code.get(str(data.get("code") or ""))
    steps = [str(s).strip()[:400] for s in (data.get("steps") or []) if str(s).strip()][:10]
    return {"entry": out(entry) if entry else None, "summary": str(data.get("summary") or "").strip()[:800],
            "steps": steps, "notes": str(data.get("notes") or "").strip()[:800], "model": result.public_model}
