"""
Eşleme stüdyosu (ADIM 12.3): ortak iş nesnesi (12.2) → bağlantıdaki hedef (Odoo modeli, MCP aracı, Edge şablonu).

Kural = bir hedef alan nasıl doldurulur:
- copy      kaynak alanı olduğu gibi (tür hedefe göre çevrilir: tarih-saat, tam sayı, metin)
- const     sabit değer
- map       kaynak değer → hedef değer tablosu (ör. STOCK → consu), default ile
- contains  liste kaynakta değer varsa true_value, yoksa false_value (ör. rol MÜŞTERİ → customer_rank 1)
- template  metin şablonu: "{name} ({code})"
- lookup    hedef sistemde kayıt arar ve kimliğini yazar (yalnızca Odoo): ör. birim "Adet" → uom.uom #1.
            values ile aday adlar (Adet → ["Adet", "Units"]), fields ile sırayla aranacak alanlar, many ile çoklu ilişki,
            optional ile bulunamazsa alan atlanır (uyarı) — yoksa hata.
- lines     kalemler (yalnızca Odoo, one2many): her kalem için iç kurallar → [[0, 0, {...}], ...]
Hedefte ek seçenekler (ADIM 13.3): note.source → yazmadan sonra kayda iç not (Odoo chatter, ör. bilete çözüm);
update_sources → mevcut kayıt güncellenirken YALNIZCA bu kaynak alanlardan gelen kurallar yazılır (ör. bilette konu/mesaj
ezilmez, yalnızca durum ve not). Zorunlu hedef alan denetimi yalnızca yeni kayıtta yapılır (mevcut kayıtta zaten doludur).
Doğrulama hedefin KENDİ alan tanımlarından yapılır (Odoo fields_get + default_get, MCP araç şeması, Edge şablon parametreleri):
sürüme göre değişen alan adları (ör. Odoo 20'de tax_ids) eşleme kaydedilirken yakalanır. Deneme (dry-run) YAZMAZ:
yalnızca okuma (arama) yapar ve hedefe gidecek değerleri, eksik zorunlu alanları ve "yeni kayıt / mevcut kaydı güncelle"
kararını gösterir.
"""
import html
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IntegrationConnection, IntegrationMapping
from app.integrations.base import ToolError
from app.services import business_objects as bo
from app.services import llm_gateway
from app.services.llm_gateway import LLMContext

logger = logging.getLogger("recorion.mappings")
SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "integration_mappings.json"
TRANSFORMS = ("copy", "const", "map", "contains", "template", "lookup", "lines")
ODOO_ONLY = ("lookup", "lines")
MAX_RULES = 80
SUPPORTED = ("odoo", "mcp", "edge")

SAMPLES: Dict[str, Dict[str, Any]] = {
    "PRODUCT": {"code": "RECT-ELT-01", "name": "RECOrion Test El Terminali", "type": "STOCK", "unit": "Adet", "sale_price": 12500,
                "purchase_price": 9800, "currency": "TRY", "vat_rate": 20, "barcode": "8690000000017", "category": "Goods",
                "description": "Depo sayımı için barkodlu el terminali (deneme kaydı)."},
    "PARTNER": {"kind": "COMPANY", "name": "RECOrion Test Makine San. Ltd. Şti.", "tax_number": "1234567890", "tax_office": "Kadıköy",
                "email": "satis@recorion-test.example", "phone": "+90 216 000 00 00", "street": "Test Cad. No:1", "district": "Kadıköy",
                "city": "İstanbul", "zip": "34710", "country": "TR", "roles": ["CUSTOMER"]},
    "ORDER": {"direction": "SALE", "stage": "QUOTE", "partner_ref": "RECOrion Test Makine San. Ltd. Şti.", "date": "2026-11-02",
              "currency": "TRY", "notes": "Deneme teklifi",
              "lines": [{"product_code": "RECT-ELT-01", "description": "El terminali", "quantity": 5, "unit": "Adet", "unit_price": 12500, "vat_rate": 20}]},
    "TASK": {"title": "RECOrion Test: depo sayımı hazırlığı", "description": "Raf etiketlerini kontrol et.", "due_date": "2026-11-15",
             "priority": "HIGH"},
    "SUPPORT_TICKET": {"subject": "RECOrion Test: kulaklık iadesi", "description": "Ürün kutusu hasarlı geldi, iade etmek istiyorum.",
                       "category": "RETURN", "channel": "TRENDYOL", "priority": "HIGH", "customer_name": "RECOrion Test Müşterisi",
                       "customer_email": "musteri@recorion-test.example", "order_ref": "TY-0000001", "product_ref": "Kulaklık",
                       "status": "OPEN"},
    "DOCUMENT": {"title": "RECOrion Test raporu", "artifact_id": "00000000-0000-0000-0000-000000000000", "description": "Deneme"},
}


# RECDx uygulamasına bağlı hazır eşlemeler: yalnızca o uygulamayı kullanan şirkete görünür (ADIM 13.3)
APP_TEMPLATES = {"odoo_helpdesk_ticket": "recqmind"}


class MappingError(Exception):
    pass


def template_visible(code: Optional[str], tenant) -> bool:
    from app.services import recdx_apps

    app = APP_TEMPLATES.get(code or "")
    return not app or (tenant is not None and recdx_apps.is_active(tenant, app))


def clean_target_options(object_type: str, target: Dict[str, Any]) -> Dict[str, Any]:
    """Hedefin ek seçenekleri: iç not kaynağı ve güncellemede yazılacak kaynak alanlar (nesnede olmayan atılır)."""
    src = {f["key"] for f in bo.OBJECTS.get(object_type, {}).get("fields", [])}
    out: Dict[str, Any] = {}
    note = target.get("note") if isinstance(target.get("note"), dict) else {}
    if note.get("source") in src:
        out["note"] = {"source": note["source"], "title": str(note.get("title") or "")[:80]}
    if isinstance(target.get("update_sources"), list):
        out["update_sources"] = [x for x in target["update_sources"] if x in src][:40]
    return out


@dataclass
class Built:
    values: Dict[str, Any] = field(default_factory=dict)
    preview: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# --- hedef bağdaştırıcıları ---

class Target:
    """Bir bağlayıcının hedef alanlarını okuyan ve (Odoo'da) arama yapan bağdaştırıcı. Hiçbir zaman yazmaz."""
    lookups = False

    def __init__(self, conn: IntegrationConnection, ctx):
        self.conn, self.ctx = conn, ctx

    async def fields(self, target: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        raise NotImplementedError

    async def lookup(self, model: str, field_: str, value: Any, domain: list) -> List[int]:
        raise MappingError("Bu sistemde arama (lookup) kuralı kullanılamaz.")

    async def find(self, target: Dict[str, Any], field_: str, value: Any) -> Optional[int]:
        return None


class OdooTarget(Target):
    lookups = True

    def __init__(self, conn, ctx):
        super().__init__(conn, ctx)
        self._cache: Dict[Any, Any] = {}

    async def _kw(self, model, method, args, kw=None):
        from app.integrations import odoo

        return await odoo._kw(self.ctx, model, method, args, kw or {})

    async def fields(self, target):
        model = str(target.get("model") or "")
        if not re.fullmatch(r"[a-z][a-z0-9_.]{1,80}", model):
            raise MappingError("Hedef Odoo modeli geçersiz (ör. product.template).")
        allowed = [m.strip() for m in (self.ctx.config.get("allowed_models") or "").split(",") if m.strip()]
        if allowed and model not in allowed:
            raise MappingError(f"'{model}' modeli bu bağlantıda izinli değil.")
        key = ("fields", model)
        if key not in self._cache:
            raw = await self._kw(model, "fields_get", [], {"attributes": ["string", "type", "required", "relation", "selection", "readonly", "depends"]})
            # Gerçekten doldurulması gereken: zorunlu, yazılabilir, hesaplanmayan (depends boş), satır listesi olmayan ve varsayılanı olmayan
            required = [n for n, f in raw.items() if f.get("required") and not f.get("readonly") and not f.get("depends")
                        and f.get("type") != "one2many"]
            defaults = await self._kw(model, "default_get", [required]) if required else {}
            out = {}
            for n, f in raw.items():
                if f.get("readonly") or n.startswith(("message_", "activity_", "website_")) or f.get("type") == "binary":
                    continue
                out[n] = {"label": f.get("string") or n, "type": f.get("type"), "relation": f.get("relation"),
                          "selection": [s[0] for s in f.get("selection") or []] or None,
                          "required": n in required and n not in (defaults or {})}
            self._cache[key] = out
        return self._cache[key]

    async def lookup(self, model, field_, value, domain):
        key = ("lookup", model, field_, json.dumps(value, default=str), json.dumps(domain))
        if key not in self._cache:
            op = "=" if isinstance(value, (int, float)) and not isinstance(value, bool) else "=ilike"
            rows = await self._kw(model, "search_read", [[[field_, op, value], *domain]], {"fields": ["id"], "limit": 2})
            self._cache[key] = [r["id"] for r in rows or []]
        return self._cache[key]

    async def find(self, target, field_, value):
        if field_ == "id":  # kayıt kimliğiyle eşleşme (ör. bilet no): tam sayı olmalı
            if not str(value).strip().isdigit():
                return None
            value = int(str(value).strip())
        ids = await self.lookup(target["model"], field_, value, [])
        return ids[0] if ids else None


def tool_result_id(result: Any) -> Optional[Any]:
    """Arama aracının sonucundan kayıt kimliği: REST şablonu {"id"}; SQL şablonu ilk satırın ilk sütunu; MCP structured id."""
    if not isinstance(result, dict):
        return None
    if result.get("id") not in (None, ""):
        return result["id"]
    rows = result.get("rows")
    if isinstance(rows, list) and rows and isinstance(rows[0], list) and rows[0]:
        return rows[0][0]
    data = result.get("data")
    if isinstance(data, dict) and data.get("id") not in (None, ""):
        return data["id"]
    return None


class ToolTarget(Target):
    """MCP aracı veya Edge şablonu: alanlar aracın giriş şemasından. Eşleştirme için target.find_tool (okuma aracı, eşleştirme
    alanıyla aynı adlı parametre alır) ve güncelleme için target.update_tool (aynı alanlar + id) tanımlanabilir."""

    async def _tool(self, name: str):
        from app.services import tool_gateway

        return next((t for t in await tool_gateway.connection_tools(self.conn) if t.name == name), None)

    async def find(self, target, field_, value):
        from app.services import tool_gateway

        name = target.get("find_tool")
        if not name:
            return None
        tool = await self._tool(name)
        if not tool:
            raise MappingError(f"Arama aracı '{name}' bu bağlantıda yok.")
        return tool_result_id(await tool.run(tool_gateway.context(self.conn), {field_: value}))

    async def fields(self, target):
        from app.services import tool_gateway

        name = str(target.get("tool") or "")
        tool = next((t for t in await tool_gateway.connection_tools(self.conn) if t.name == name), None)
        if not tool:
            raise MappingError(f"Bu bağlantıda '{name}' aracı yok.")
        schema = tool.input_schema or {}
        req = set(schema.get("required") or [])
        return {n: {"label": p.get("title") or p.get("description") or n, "type": p.get("type") or "string", "relation": None,
                    "selection": p.get("enum"), "required": n in req}
                for n, p in (schema.get("properties") or {}).items() if isinstance(p, dict)}


def adapter(conn: IntegrationConnection) -> Target:
    from app.services import tool_gateway

    if conn.connector not in SUPPORTED:
        raise MappingError("Bu sistem türü için eşleme desteklenmiyor (Odoo, MCP sunucusu veya Edge Connector).")
    ctx = tool_gateway.context(conn)
    return OdooTarget(conn, ctx) if conn.connector == "odoo" else ToolTarget(conn, ctx)


# --- doğrulama ---

def _source_fields(object_type: str, nested: bool = False) -> Dict[str, Dict[str, Any]]:
    spec = bo.OBJECTS[object_type]["fields"]
    if nested:
        lines = next(f for f in spec if f["type"] == "lines")
        return {f["key"]: f for f in lines["fields"]}
    return {f["key"]: f for f in spec}


def clean_rules(rules: Any, nested: bool = False) -> List[Dict[str, Any]]:
    if not isinstance(rules, list):
        raise MappingError("Kurallar liste olmalı.")
    out = []
    for r in rules[:MAX_RULES]:
        if not isinstance(r, dict) or not r.get("target"):
            continue
        t = r.get("transform") or "copy"
        if t not in TRANSFORMS or (nested and t == "lines"):
            raise MappingError(f"'{r.get('target')}' için dönüşüm geçersiz: {t}")
        params = r.get("params") if isinstance(r.get("params"), dict) else {}
        if t == "lines":
            params = {**params, "rules": clean_rules(params.get("rules") or [], nested=True)}
        out.append({"target": str(r["target"])[:80], "transform": t, "source": (str(r["source"])[:40] if r.get("source") else None),
                    "params": params})
    return out


def check(object_type: str, rules: List[Dict[str, Any]], fields: Dict[str, Dict[str, Any]], connector: str,
          match: Optional[Dict[str, Any]] = None, nested: bool = False) -> Tuple[List[str], List[str]]:
    """Kuralları hedefin alanlarına ve nesnenin şemasına göre denetler. Dönüş: (hatalar, uyarılar)."""
    errors, warnings = [], []
    src = _source_fields(object_type, nested)
    seen = set()
    for r in rules:
        tgt, t, s = r["target"], r["transform"], r.get("source")
        label = f"'{tgt}'"
        if tgt in seen:
            errors.append(f"{label} alanı iki kez eşlenmiş.")
        seen.add(tgt)
        if tgt not in fields:
            errors.append(f"Hedefte {label} alanı yok (veya yazılamaz).")
            continue
        if t in ODOO_ONLY and connector != "odoo":
            errors.append(f"{label}: '{t}' yalnızca Odoo bağlantılarında kullanılabilir.")
        if t in ("copy", "map", "contains", "lookup", "lines") and (not s or s not in src):
            errors.append(f"{label}: kaynak alan geçersiz ({s or 'boş'}).")
        if t == "const" and "value" not in r["params"]:
            errors.append(f"{label}: sabit değer girilmemiş.")
        if t == "template" and not r["params"].get("text"):
            errors.append(f"{label}: metin şablonu boş.")
        if t == "template":
            for k in re.findall(r"\{(\w+)\}", r["params"].get("text") or ""):
                if k not in src:
                    errors.append(f"{label}: şablondaki {{{k}}} nesnede yok.")
        if t == "lookup" and connector == "odoo":
            rel = fields[tgt].get("relation")
            if not (r["params"].get("model") or rel):
                errors.append(f"{label}: arama için ilişkili model yok (alan ilişki alanı değil).")
            if fields[tgt].get("type") == "many2many" and not r["params"].get("many"):
                r["params"]["many"] = True
        if t == "lines" and fields[tgt].get("type") != "one2many":
            errors.append(f"{label}: kalemler yalnızca satır (one2many) alanına yazılabilir.")
        sel = fields[tgt].get("selection")
        if sel:
            produced = [r["params"].get("value")] if t == "const" else list((r["params"].get("values") or {}).values()) if t == "map" else []
            bad = [v for v in produced if v is not None and v not in sel]
            if bad:
                errors.append(f"{label}: {', '.join(map(str, bad))} hedefte geçerli değil (geçerli: {', '.join(map(str, sel))}).")
    if not nested:
        missing = [f"{n} ({f['label']})" for n, f in fields.items() if f.get("required") and n not in seen]
        if missing:
            warnings.append("Eşlenmemiş zorunlu alan: " + ", ".join(missing[:10]))
        if match:
            if match.get("source") not in src or (match.get("target") not in fields and not (connector == "odoo" and match.get("target") == "id")):
                errors.append("Eşleştirme alanı geçersiz (tekrar aktarımda aynı kaydı bulmak için kaynak ve hedef alan).")
    return errors, warnings


# --- değer üretimi ---

def _odoo_value(value: Any, ftype: Optional[str]) -> Any:
    if value is None:
        return None
    if ftype == "datetime" and isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return f"{value} 00:00:00"
    if ftype == "html" and isinstance(value, str):
        return "<p>" + html.escape(value).replace("\n", "<br/>") + "</p>"
    if ftype in ("integer",) and isinstance(value, float):
        return int(round(value))
    if ftype in ("char", "text") and not isinstance(value, str):
        return str(value)
    return value


def _schema_value(value: Any, ftype: Optional[str]) -> Any:
    if ftype == "integer" and isinstance(value, float):
        return int(round(value))
    if ftype == "string" and not isinstance(value, str) and value is not None:
        return str(value)
    return value


def _fmt(text: str, obj: Dict[str, Any]) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: "" if obj.get(m.group(1)) is None else str(obj.get(m.group(1))), text).strip()


async def _rule_value(rule, obj, finfo, tgt: Target, out: Built, prefix: str = "") -> Tuple[bool, Any]:
    """(yazılsın mı, değer)"""
    t, s, p = rule["transform"], rule.get("source"), rule["params"]
    label = f"{prefix}{finfo.get('label') or rule['target']}"
    v = obj.get(s) if s else None
    if t == "const":
        return True, p.get("value")
    if t == "template":
        text = _fmt(p.get("text") or "", obj)
        return bool(text), text
    if v in (None, "", []):
        return False, None
    if t == "copy":
        return True, v
    if t == "map":
        table = p.get("values") or {}
        key = str(v)
        if key in table:
            return True, table[key]
        if "default" in p:
            return True, p["default"]
        out.errors.append(f"{label}: '{v}' için karşılık tanımlı değil.")
        return False, None
    if t == "contains":
        items = v if isinstance(v, list) else [v]
        return True, p.get("true_value", True) if p.get("value") in items else p.get("false_value", False)
    if t == "lookup":
        model = p.get("model") or finfo.get("relation")
        many = bool(p.get("many"))
        wanted = v if isinstance(v, list) else [v]
        ids = []
        for item in wanted:
            cands = (p.get("values") or {}).get(str(item), [item])
            cands = cands if isinstance(cands, list) else [cands]
            found = None
            for fld in (p.get("fields") or [p.get("field") or "name"]):
                for c in cands:
                    hit = await tgt.lookup(model, fld, c, p.get("domain") or [])
                    if hit:
                        found = hit[0]
                        break
                if found:
                    break
            shown = int(item) if isinstance(item, float) and item.is_integer() else item
            if found:
                ids.append(found)
            elif p.get("optional"):
                out.warnings.append(f"{label}: '{shown}' hedefte bulunamadı; alan boş bırakıldı.")
            else:
                out.errors.append(f"{label}: '{shown}' hedefte ({model}) bulunamadı.")
        if not ids:
            return False, None
        return True, ([[6, 0, ids]] if many else ids[0])
    if t == "lines":
        rows = []
        lfields = await tgt.fields({"model": finfo.get("relation")}) if finfo.get("relation") else {}
        for i, line in enumerate(v if isinstance(v, list) else [], 1):
            vals = {}
            for lr in p.get("rules") or []:
                lf = lfields.get(lr["target"], {})
                ok, lv = await _rule_value(lr, line, lf, tgt, out, prefix=f"{i}. kalem — ")
                if ok:
                    vals[lr["target"]] = _odoo_value(lv, lf.get("type"))
            rows.append([0, 0, vals])
        return bool(rows), rows
    return False, None


def _display(v: Any) -> str:
    if isinstance(v, list) and v and isinstance(v[0], list) and len(v[0]) == 3:
        return f"{len(v)} satır" if v[0][0] == 0 else f"kayıt #{', #'.join(map(str, v[0][2]))}"
    return str(v)[:200]


async def build(mapping: IntegrationMapping, obj: Dict[str, Any], tgt: Target, update: bool = False) -> Built:
    """Nesneden hedefe gidecek değerleri üretir (aramalar okuma; YAZMA YOK). update: mevcut kayıt güncellenecek."""
    out = Built()
    only = (mapping.target or {}).get("update_sources") if update else None
    clean, errs = bo.validate(mapping.object_type, obj)
    out.errors += errs
    try:
        fields = await tgt.fields(mapping.target)
    except (ToolError, MappingError) as exc:
        out.errors.append(str(exc))
        return out
    for rule in mapping.rules or []:
        if only is not None and rule.get("source") not in only:
            continue
        finfo = fields.get(rule["target"], {})
        try:
            ok, v = await _rule_value(rule, clean, finfo, tgt, out)
        except (ToolError, MappingError) as exc:
            out.errors.append(f"{rule['target']}: {exc}")
            continue
        if not ok:
            continue
        v = _odoo_value(v, finfo.get("type")) if mapping.connector == "odoo" else _schema_value(v, finfo.get("type"))
        out.values[rule["target"]] = v
        out.preview.append({"target": rule["target"], "label": finfo.get("label") or rule["target"], "value": _display(v),
                            "source": rule.get("source"), "transform": rule["transform"]})
    missing = [f"{n} ({f['label']})" for n, f in fields.items() if f.get("required") and n not in out.values]
    if missing and not update:
        out.errors.append("Hedefte zorunlu ama boş kalan alan: " + ", ".join(missing[:10]))
    note = (mapping.target or {}).get("note") or {}
    if note.get("source") and clean.get(note["source"]):
        out.preview.append({"target": "(iç not)", "label": note.get("title") or "İç not", "value": str(clean[note["source"]])[:200],
                            "source": note["source"], "transform": "note"})
    if update and not out.values and not (note.get("source") and clean.get(note["source"])):
        out.errors.append("Mevcut kayıtta güncellenecek bir değer yok.")
    return out


async def existing_id(mapping: IntegrationMapping, obj: Dict[str, Any], tgt: Target) -> Optional[Any]:
    """Eşleştirme alanıyla hedefteki mevcut kayıt (yoksa None). Arama hatası çağırana iletilir."""
    m = mapping.match or {}
    if not m.get("source") or obj.get(m["source"]) in (None, ""):
        return None
    found = await tgt.find(mapping.target, m["target"], obj[m["source"]])
    return None if found in (None, "") else found


def applies(mapping: IntegrationMapping, obj: Dict[str, Any]) -> bool:
    w = mapping.when or {}
    return not w or str(obj.get(w.get("field"))) == str(w.get("equals"))


async def dry_run(mapping: IntegrationMapping, conn: IntegrationConnection, sample: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    obj = sample or SAMPLES.get(mapping.object_type) or {}
    tgt = adapter(conn)
    existing, warn = None, None
    try:
        existing = await existing_id(mapping, bo.validate(mapping.object_type, obj)[0] or obj, tgt)
    except (ToolError, MappingError) as exc:
        warn = f"Mevcut kayıt aranamadı: {exc}"
    built = await build(mapping, obj, tgt, update=existing is not None)
    if warn:
        built.warnings.append(warn)
    action = "UPDATE" if existing is not None else "CREATE"
    if not applies(mapping, obj):
        built.warnings.append("Bu örnek, eşlemenin koşuluna uymuyor; gerçek aktarımda bu eşleme kullanılmaz.")
    return {"ok": not built.errors, "at": datetime.now(timezone.utc).isoformat(), "version": mapping.version, "sample": bo.mask_pii(mapping.object_type, obj),
            "values": built.values, "preview": built.preview, "errors": built.errors, "warnings": built.warnings,
            "action": action, "existing_id": existing}


# --- hazır eşlemeler ---

async def ensure_templates(db: AsyncSession, path: Path = SEED_FILE) -> int:
    if not path.exists():
        return 0
    have = set((await db.execute(select(IntegrationMapping.code).where(IntegrationMapping.code.isnot(None)))).scalars())
    added = 0
    for t in json.loads(path.read_text(encoding="utf-8")):
        if t["code"] in have:
            continue
        db.add(IntegrationMapping(tenant_id=None, code=t["code"], connector=t["connector"], object_type=t["object_type"], name=t["name"],
                                  description=t.get("description"), target=t["target"], rules=clean_rules(t["rules"]),
                                  match=t.get("match"), when=t.get("when"), status="ACTIVE"))
        added += 1
    await db.commit()
    return added


# --- RECAi önerisi ---

SUGGEST_PROMPT = """Sen RECAi'sin: RECOrion'un ortak iş nesnesini şirketin sistemindeki hedefe eşleyeceksin.
Kurallar listesi üret. Dönüşümler: copy (kaynak alan), const (sabit: params.value), map (params.values: kaynak→hedef, params.default),
contains (liste kaynakta params.value varsa params.true_value yoksa params.false_value), template (params.text, ör. "{{name}} ({{code}})"),
{odoo_only}
Yalnızca aşağıdaki HEDEF ALANLARINI ve KAYNAK ALANLARINI kullan; alan uydurma. Seçenekli hedef alanda yalnızca listelenen değerleri yaz.
Zorunlu hedef alanları mutlaka doldur. Tekrar aktarımda aynı kaydı bulmak için uygun bir "match" seç (ör. stok kodu, VKN) veya null.
Yanıtın YALNIZCA şu JSON olsun:
{{"rules": [{{"target": "hedef_alan", "transform": "copy", "source": "kaynak_alan", "params": {{}}}}], "match": {{"source": "...", "target": "..."}},
  "notes": "kısa açıklama: neyi neden böyle eşledin, dikkat edilecekler"}}
"""
ODOO_ONLY_HINT = ("lookup (ilişki alanı: hedef sistemde ara; params.fields aranacak alanlar ör. [\"name\"], params.values kaynak değer→aday adlar "
                  "listesi ör. {\"Adet\": [\"Adet\", \"Units\"]}, params.many çoklu, params.optional bulunamazsa atla, params.domain ek filtre), "
                  "lines (kalemler: params.rules iç kurallar, kaynak 'lines').")


async def relation_samples(tgt: Target, fields: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Küçük ilişki tablolarından örnek değerler (birim, vergi, kategori) — AI'ın aday ad tablosu kurabilmesi için."""
    out = {}
    if not isinstance(tgt, OdooTarget):
        return out
    small = {"uom.uom": ["name"], "account.tax": ["name", "amount", "type_tax_use"], "product.category": ["name"], "res.currency": ["name"]}
    for rel in {f["relation"] for f in fields.values() if f.get("relation") in small}:
        try:
            rows = await tgt._kw(rel, "search_read", [[]], {"fields": small[rel], "limit": 40})
            out[rel] = [" · ".join(str(r.get(k)) for k in small[rel]) for r in rows]
        except (ToolError, MappingError):
            continue
    return out


def _brief(fields: Dict[str, Dict[str, Any]], limit: int = 120) -> str:
    keys = sorted(fields, key=lambda n: (not fields[n].get("required"), n))[:limit]
    return "\n".join(f"- {n}: {fields[n]['label']} [{fields[n].get('type')}{', zorunlu' if fields[n].get('required') else ''}"
                     f"{', ilişki ' + fields[n]['relation'] if fields[n].get('relation') else ''}"
                     f"{', seçenekler ' + '/'.join(map(str, fields[n]['selection'][:12])) if fields[n].get('selection') else ''}]" for n in keys)


async def suggest(tenant_id: uuid.UUID, conn: IntegrationConnection, object_type: str, target: Dict[str, Any]) -> Dict[str, Any]:
    tgt = adapter(conn)
    fields = await tgt.fields(target)
    src = bo.OBJECTS[object_type]["fields"]
    lines = next((f for f in src if f["type"] == "lines"), None)
    samples = await relation_samples(tgt, fields)
    parts = [SUGGEST_PROMPT.format(odoo_only=ODOO_ONLY_HINT if conn.connector == "odoo" else "(lookup ve lines bu sistemde KULLANILAMAZ)."),
             f"NESNE: {object_type} ({bo.OBJECTS[object_type]['label']})\nKAYNAK ALANLARI:",
             "\n".join(f"- {f['key']}: {f['label']} [{f['type']}{', seçenekler ' + '/'.join(f['options']) if f.get('options') else ''}]" for f in src)]
    if lines:
        parts.append("KALEM ALANLARI (lines içinde): " + ", ".join(f"{f['key']} ({f['label']})" for f in lines["fields"]))
    parts.append(f"HEDEF: {json.dumps(target, ensure_ascii=False)}\nHEDEF ALANLARI:\n{_brief(fields)}")
    if lines and conn.connector == "odoo":
        line_field = next((n for n, f in fields.items() if f.get("type") == "one2many" and n in ("order_line", "line_ids", "invoice_line_ids")), None)
        if line_field:
            lf = await tgt.fields({"model": fields[line_field]["relation"]})
            parts.append(f"KALEM HEDEF ALANLARI ({line_field} → {fields[line_field]['relation']}):\n{_brief(lf, 60)}")
    if samples:
        parts.append("HEDEF SİSTEMDEKİ ÖRNEK DEĞERLER:\n" + "\n".join(f"- {k}: {', '.join(v)}" for k, v in samples.items()))
    ctx = LLMContext(tenant_id=tenant_id, purpose="BRAIN", task_type="STRUCTURED")
    messages = [{"role": "user", "content": "\n\n".join(parts)}]
    data = None
    for _ in range(2):
        result = await llm_gateway.chat(ctx, messages, temperature=0.1, max_tokens=4000, timeout=240, fallback=True)
        m = re.search(r"\{.*\}", result.content or "", re.S)
        try:
            data = json.loads(m.group(0)) if m else None
        except ValueError:
            data = None
        if isinstance(data, dict) and isinstance(data.get("rules"), list):
            break
        messages += [{"role": "assistant", "content": result.content or ""}, {"role": "user", "content": "Yalnızca istenen JSON'u ver."}]
    if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
        raise MappingError("RECAi şu an eşleme önerisi üretemedi; biraz sonra yeniden deneyin.")
    try:
        rules = clean_rules(data["rules"])
    except MappingError:
        rules = []
    # Hedefte olmayan alanlara yazan kurallar atılır (uydurma alan kayda girmez)
    kept = [r for r in rules if r["target"] in fields and (r["transform"] not in ODOO_ONLY or conn.connector == "odoo")]
    match = data.get("match") if isinstance(data.get("match"), dict) else None
    errors, warnings = check(object_type, kept, fields, conn.connector, match)
    return {"rules": kept, "match": match, "notes": str(data.get("notes") or "")[:1000], "dropped": len(rules) - len(kept),
            "errors": errors, "warnings": warnings, "model": result.public_model}
