"""
RECDx uygulamaları (ADIM 13.1): RECDx'in Odoo üzerinde çalışan ürünleriyle entegrasyon ve satış.

- RECQmind: pazar yeri (Trendyol, Hepsiburada, Amazon...) e-postalarından Odoo Helpdesk bileti açan AI destek masası.
- RECSlip: masraf fişlerini AI ile okuyup ön muhasebe kaydı hazırlayan Odoo uygulaması (LUCA/Logo aktarımı).

Satış modeli (kullanıcı kararı 25.10.2026, karma): uygulamalar Odoo Apps'te liste fiyatıyla satılır; RECOrion paketinde paket
tanımındaki teklifle sunulur — NONE (yok), DISCOUNT (yüzde indirim), INCLUDED (dahil). Teklifin Odoo ürünü Süper Admin
tarafından paket tanımında Odoo'dan seçilir (paketin kendi ürünü gibi); fiyatlı veya fiyatsız olabilir.
Müşteri seçimi (satın almada veya sonra Şirket Yönetimi'nde), her uygulama için:
- USING  zaten kullanıyorum → yalnızca entegrasyon/MCP açılır, satış yok
- ADD    paketime ekle (paketin teklifi varsa) → Odoo satış siparişine satır (dahilse 0 fiyat, indirimliyse indirimli)
- QUOTE  teklif iste → Odoo CRM fırsatı
- NO     istemiyorum
Odoo'su olmayan şirket USING/ADD seçemez (teklife döner). Entegrasyon yalnızca Odoo varsa ve USING/ADD ise açılır.
Her seçim recdx_app_requests'e yazılır ve Genel Merkez (Süper Admin) ekranında izlenir.
"""
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan, RecdxAppRequest, Tenant, TenantLead

logger = logging.getLogger("recorion.recdx_apps")

APPS: Dict[str, Dict[str, Any]] = {
    "recqmind": {"title": "RECQmind", "subtitle": "Pazar yeri AI destek masası (Odoo Helpdesk)",
                 "description": "Trendyol, Hepsiburada, Amazon gibi pazar yerlerinden e-postayla gelen sipariş, soru, problem ve iade "
                                "bildirimlerini Odoo Helpdesk'te bilete dönüştürür, sınıflandırır ve önceliklendirir.",
                 "with_recorion": "İade, iptal, kargo problemi gibi birden çok kişi gerektiren biletler RECOrion'da Case olarak açılır; "
                                  "AI personel siparişi ve stoğu inceler, yanıt taslağı hazırlar, sonuç onayla Odoo biletine yazılır.",
                 "url": "https://www.recdx.com/recqmind", "store_url": "https://apps.odoo.com/apps/modules/19.0/recqmind"},
    "recslip": {"title": "RECSlip", "subtitle": "AI masraf fişi ve ön muhasebe (Odoo)",
                "description": "Masraf fişlerini AI ile okur, şirketin faaliyet alanına göre hesaplara ayırır, onaydan sonra LUCA/Logo'ya "
                               "aktarım dosyası hazırlar.",
                "with_recorion": "Sorunlu fişler (mükerrer, eksik VKN, düşük güven) RECOrion'da Case olur; ay sonu kapanış kontrolü "
                                 "otomatik açılır, eksikler ve onay bekleyenler takip edilir.",
                "url": "https://www.recdx.com/recslip-mukellef", "store_url": "https://apps.odoo.com/apps/modules/19.0/recslip"},
}
CHOICES = ("USING", "ADD", "QUOTE", "NO")
CHOICE_LABELS = {"USING": "Zaten kullanıyorum", "ADD": "Paketime ekle", "QUOTE": "Teklif istiyorum", "NO": "Hayır"}
MODES = ("NONE", "DISCOUNT", "INCLUDED")
OPEN = ("NEW", "ORDERED", "OPPORTUNITY", "IN_USE")
_tasks: set = set()


def now() -> datetime:
    return datetime.now(timezone.utc)


# --- paket teklifi ---

def clean_offer(raw: Any) -> Dict[str, Dict[str, Any]]:
    """Süper Admin'in paket tanımındaki uygulama teklifleri."""
    raw = raw if isinstance(raw, dict) else {}
    out = {}
    for code in APPS:
        r = raw.get(code) if isinstance(raw.get(code), dict) else {}
        mode = str(r.get("mode") or "NONE").upper()
        if mode not in MODES:
            raise ValueError(f"{APPS[code]['title']}: teklif türü geçersiz.")
        item: Dict[str, Any] = {"mode": mode}
        if mode == "DISCOUNT":
            try:
                d = float(r.get("discount"))
            except (TypeError, ValueError):
                raise ValueError(f"{APPS[code]['title']}: indirim yüzdesi girilmeli.")
            if not 0 < d < 100:
                raise ValueError(f"{APPS[code]['title']}: indirim 0 ile 100 arasında olmalı.")
            item["discount"] = round(d, 2)
        if mode != "NONE" and r.get("odoo_product_id"):
            item["odoo_product_id"] = int(r["odoo_product_id"])
            item["odoo_product_name"] = str(r.get("odoo_product_name") or "")[:255]
            item["list_price"] = float(r.get("list_price") or 0)
        out[code] = item
    return out


def offer(plan: Optional[Plan], code: str) -> Dict[str, Any]:
    """Paketin bu uygulama için teklifi ve müşteriye fiyatı (liste fiyatı Odoo ürününden)."""
    o = dict(((plan.recdx_apps if plan else None) or {}).get(code) or {"mode": "NONE"})
    o.setdefault("mode", "NONE")
    lp = Decimal(str(o.get("list_price") or 0))
    if o["mode"] == "INCLUDED":
        price = Decimal(0)
    elif o["mode"] == "DISCOUNT":
        price = (lp * (Decimal(100) - Decimal(str(o.get("discount") or 0))) / Decimal(100)).quantize(Decimal("0.01"))
    else:
        price = None
    o["price"] = float(price) if price is not None else None
    o["available"] = o["mode"] != "NONE"
    return o


# --- müşteri tercihi ---

def clean(raw: Any, plan: Optional[Plan] = None) -> Dict[str, Any]:
    """Gelen tercihi doğrular. Odoo yoksa USING/ADD → QUOTE; paketin teklifi yoksa ADD → QUOTE. Eski 'INTERESTED' = QUOTE."""
    raw = raw if isinstance(raw, dict) else {}
    has_odoo = raw.get("has_odoo")
    has_odoo = bool(has_odoo) if has_odoo is not None else None
    apps = {}
    for code in APPS:
        v = str((raw.get("apps") or {}).get(code) or "").upper()
        v = "QUOTE" if v == "INTERESTED" else v
        if v not in CHOICES:
            continue
        if v in ("USING", "ADD") and has_odoo is False:
            v = "QUOTE"
        if v == "ADD" and plan is not None and not offer(plan, code)["available"]:
            v = "QUOTE"
        apps[code] = v
    return {"has_odoo": has_odoo, "apps": apps}


def get(tenant: Optional[Tenant]) -> Dict[str, Any]:
    pref = ((tenant.settings or {}) if tenant is not None else {}).get("recdx_apps") or {}
    apps = {k: ("QUOTE" if v == "INTERESTED" else v) for k, v in (pref.get("apps") or {}).items()}
    return {"has_odoo": pref.get("has_odoo"), "apps": apps, "updated_at": pref.get("updated_at")}


def is_active(tenant: Tenant, code: str) -> bool:
    """Entegrasyon (katalog kartı, hazır eşleme ve kurallar) açık mı: Odoo var ve uygulama kullanılıyor/eklendi."""
    pref = get(tenant)
    return bool(pref["has_odoo"]) and pref["apps"].get(code) in ("USING", "ADD")


def store(tenant: Tenant, pref: Dict[str, Any], actor_id=None, plan: Optional[Plan] = None) -> Dict[str, Any]:
    data = {**clean(pref, plan), "updated_at": now().isoformat(), "updated_by": str(actor_id) if actor_id else None}
    tenant.settings = {**(tenant.settings or {}), "recdx_apps": data}
    return data


def describe(tenant: Optional[Tenant] = None, connections: Optional[list] = None, plan: Optional[Plan] = None,
             requests: Optional[List[RecdxAppRequest]] = None) -> Dict[str, Any]:
    """Ekran için: uygulamalar, paketin teklifi, şirketin seçimi, durum ve son talep."""
    pref = get(tenant)
    odoo_connected = any(c.connector == "odoo" and c.status == "ACTIVE" for c in (connections or []))
    last = {}
    def when(r) -> datetime:  # yeni eklenen talep bellekte saat dilimsiz (utcnow), veritabanından gelen saat dilimli
        t = r.created_at or now()
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)

    for r in sorted(requests or [], key=when):
        last[r.app] = request_out(r)
    out = []
    for code, a in APPS.items():
        choice = pref["apps"].get(code)
        if pref["has_odoo"] and choice in ("USING", "ADD"):
            state = "ACTIVE" if odoo_connected else "NEEDS_ODOO"
        elif choice == "QUOTE":
            state = "QUOTE"
        else:
            state = "OFF"
        out.append({"code": code, **a, "offer": offer(plan, code) if plan is not None else None, "choice": choice, "state": state,
                    "request": last.get(code)})
    return {"has_odoo": pref["has_odoo"], "updated_at": pref.get("updated_at"), "odoo_connected": odoo_connected, "apps": out,
            "choices": CHOICE_LABELS}


# --- talepler ---

def request_out(r: RecdxAppRequest, tenant_name: Optional[str] = None) -> Dict[str, Any]:
    return {"id": str(r.id), "tenant_id": str(r.tenant_id), "tenant_name": tenant_name, "app": r.app, "app_title": APPS.get(r.app, {}).get("title"),
            "choice": r.choice, "choice_label": CHOICE_LABELS.get(r.choice), "source": r.source, "mode": r.mode,
            "discount": float(r.discount) if r.discount is not None else None, "list_price": float(r.list_price) if r.list_price is not None else None,
            "price": float(r.price) if r.price is not None else None, "odoo_order_name": r.odoo_order_name, "odoo_order_id": r.odoo_order_id,
            "odoo_lead_id": r.odoo_lead_id, "status": r.status, "error": r.error, "note": r.note, "created_at": r.created_at}


async def create_requests(db: AsyncSession, tenant: Tenant, plan: Optional[Plan], choices: Dict[str, str], source: str,
                          lead: Optional[TenantLead] = None, actor_id=None) -> List[RecdxAppRequest]:
    """Yeni seçimler için talep açar (aynı uygulama + seçim için açık talep varsa yenisi açılmaz). Çağıran commit eder."""
    existing = (await db.execute(select(RecdxAppRequest).where(RecdxAppRequest.tenant_id == tenant.id,
                                                               RecdxAppRequest.status.in_(OPEN)))).scalars().all()
    made = []
    for code, choice in choices.items():
        if choice not in ("USING", "ADD", "QUOTE") or any(r.app == code and r.choice == choice for r in existing):
            continue
        o = offer(plan, code)
        r = RecdxAppRequest(tenant_id=tenant.id, lead_id=lead.id if lead else None, plan_id=plan.id if plan else None, app=code,
                            choice=choice, source=source, mode=o["mode"], discount=o.get("discount"), list_price=o.get("list_price"),
                            price=o["price"] if choice == "ADD" else None, odoo_product_id=o.get("odoo_product_id") if choice in ("ADD", "QUOTE") else None,
                            status="IN_USE" if choice == "USING" else "NEW", created_by_actor_id=actor_id)
        db.add(r)
        made.append(r)
    return made


def order_lines(requests: List[RecdxAppRequest]) -> List[Dict[str, Any]]:
    """'Paketime ekle' talepleri için Odoo sipariş satırları (ürünü seçilmemiş teklif satır üretmez → Genel Merkez'de hata)."""
    lines = []
    for r in requests:
        if r.choice == "ADD" and r.odoo_product_id:
            label = "dahil" if r.mode == "INCLUDED" else f"%{float(r.discount or 0):g} indirimli"
            lines.append({"request": r, "product_id": r.odoo_product_id, "price": float(r.price or 0),
                          "name": f"{APPS[r.app]['title']} 4 RECOrion ({label})"})
    return lines


async def process_company_requests(request_ids: List[str]) -> None:
    """Şirket Yönetimi'nden gelen talepler (arka planda): ADD → yeni Odoo teklifi; QUOTE → Odoo CRM fırsatı."""
    from app.config import settings
    from app.services.odoo_service import OdooService

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        rows = [await db.get(RecdxAppRequest, rid) for rid in request_ids]
        rows = [r for r in rows if r and r.status == "NEW"]
        if not rows:
            return
        tenant = await db.get(Tenant, rows[0].tenant_id)
        if not settings.ODOO_SYNC_ENABLED:
            for r in rows:
                r.status, r.note = "SKIPPED", "Odoo eşitlemesi kapalı; Genel Merkez elle takip eder."
            await db.commit()
            return
        try:
            partner_id = await partner_for(db, tenant)
        except Exception as exc:
            for r in rows:
                r.status, r.error = "FAILED", f"Odoo müşteri kaydı bulunamadı/açılamadı: {exc}"[:500]
            await db.commit()
            return
        adds = [r for r in rows if r.choice == "ADD"]
        lines = order_lines(adds)
        for r in adds:
            if not r.odoo_product_id:
                r.status, r.error = "FAILED", "Paket tanımında bu uygulamanın Odoo ürünü seçilmemiş."
        if lines:
            res = await asyncio.to_thread(OdooService.create_quotation, partner_id, lines, f"RECOrion - {tenant.name}: RECDx uygulamaları")
            for ln in lines:
                r = ln["request"]
                if res.get("success"):
                    r.status, r.odoo_order_id, r.odoo_order_name, r.error = "ORDERED", res["order_id"], res["order_name"], None
                else:
                    r.status, r.error = "FAILED", str(res.get("error"))[:500]
        for r in rows:
            if r.choice == "QUOTE":
                await crm_opportunity(r, tenant, partner_id)
        await db.commit()


async def crm_opportunity(r: RecdxAppRequest, tenant: Tenant, partner_id: Optional[int]) -> None:
    from app.services.odoo_service import OdooService

    a = APPS[r.app]
    desc = (f"{tenant.name} RECOrion'dan {a['title']} için teklif istedi.\nPaket teklifi: {r.mode}"
            f"{f' (%{float(r.discount):g} indirim)' if r.discount else ''}.\n{a['with_recorion']}")
    res = await asyncio.to_thread(OdooService.create_crm_lead, partner_id, f"{a['title']} 4 RECOrion - {tenant.name}", desc,
                                  float(r.list_price or 0), tenant.contact_email, tenant.phone)
    if res.get("success"):
        r.status, r.odoo_lead_id, r.error = "OPPORTUNITY", res["lead_id"], None
    else:
        r.status, r.error = "FAILED", str(res.get("error"))[:500]


async def partner_for(db: AsyncSession, tenant: Tenant) -> int:
    """Şirketin Odoo müşteri kaydı: başvurudaki eşleşme, yoksa bul/aç."""
    from app.services.odoo_service import OdooService

    lead = (await db.execute(select(TenantLead).where(TenantLead.tenant_id == tenant.id, TenantLead.odoo_partner_id.isnot(None))
                             .order_by(TenantLead.created_at.desc()))).scalars().first()
    if lead:
        return lead.odoo_partner_id
    p = await asyncio.to_thread(OdooService.get_or_create_partner, tenant.name, tenant.contact_email or "", tenant.phone or "",
                                tenant.address, tenant.website, tenant.tax_id)
    if not p:
        raise RuntimeError("Odoo müşteri kaydı oluşturulamadı.")
    return p["id"]


def spawn(coro) -> None:
    t = asyncio.create_task(coro)
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)
