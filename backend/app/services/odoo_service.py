import os
import re
import xmlrpc.client
import logging
from datetime import date, datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("recorion_odoo")


class OdooUnavailable(Exception):
    pass


class OdooService:
    """
    RECOrion - Odoo 19 Entegrasyon Servisi.
    res.partner ve sale.order modüllerini yönetir.
    """

    @classmethod
    def get_config(cls) -> Dict[str, str]:
        """
        Odoo 19 bağlantı parametrelerini dinamik olarak .env ortam değişkenlerinden okur.
        Hiçbir şifre veya kimlik bilgisi kod içinde sabit tutulmaz.
        """
        return {
            "url": (os.getenv("ODOO_URL") or "").rstrip("/"),
            "db": os.getenv("ODOO_DB") or "",
            "user": os.getenv("ODOO_USER") or "",
            "password": os.getenv("ODOO_PASSWORD") or ""
        }

    @classmethod
    def _get_connection(cls):
        cfg = cls.get_config()
        if not (cfg["url"] and cfg["db"] and cfg["user"] and cfg["password"]):
            logger.error("Odoo bağlantı değişkenleri eksik! Lütfen .env dosyasında ODOO_URL, ODOO_DB, ODOO_USER ve ODOO_PASSWORD alanlarını tanımlayınız.")
            return None, None, None

        try:
            common = xmlrpc.client.ServerProxy(f"{cfg['url']}/xmlrpc/2/common")
            uid = common.authenticate(cfg["db"], cfg["user"], cfg["password"], {})
            if not uid:
                logger.error(f"Odoo kimlik doğrulama başarısız oldu (Kullanıcı: {cfg['user']}).")
                return None, None, None
            models = xmlrpc.client.ServerProxy(f"{cfg['url']}/xmlrpc/2/object")
            return uid, models, cfg
        except Exception as e:
            logger.error(f"Odoo sunucusuna bağlanırken hata: {e}")
            return None, None, None

    @classmethod
    def get_or_create_partner(
        cls,
        company_name: str,
        contact_email: str,
        phone: str,
        address: Optional[str] = None,
        website: Optional[str] = None,
        tax_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Odoo'da müşteriyi bulur, yoksa açar. Dönen sözlük: {id, name, matched_by}.

        Eşleştirme sırası (yanlış müşteriye sipariş açılmasını önlemek için):
        1. Aynı vergi numarası, ancak firma adı benziyor veya e-posta alan adı aynıysa
           (Odoo'da aynı numarayı taşıyan deneme/kirli kayıtlar başka şirketle eşleşmesin)
        2. Aynı e-posta adresi
        3. Aynı firma adı
        4. Hiçbiri yoksa yeni müşteri
        """
        uid, models, cfg = cls._get_connection()
        if not uid or not models:
            return None

        def search(domain):
            return models.execute_kw(cfg['db'], uid, cfg['password'], 'res.partner', 'search_read', [domain],
                                     {'fields': ['id', 'name', 'email', 'vat'], 'limit': 20})

        try:
            vat = (tax_id or "").replace(" ", "")
            if vat.isdigit() and len(vat) in (10, 11):
                for p in search(['|', ['vat', '=', vat], ['vat', '=', f"TR{vat}"]]):
                    if partner_matches(company_name, contact_email, p):
                        return cls._found(p, "vat", company_name)
                    logger.warning(f"Odoo'da aynı vergi numaralı ama farklı firma atlandı: ID={p['id']} '{p['name']}' (aranan: {company_name})")
            if contact_email:
                found = search([['email', '=ilike', contact_email]])
                if found:
                    return cls._found(found[0], "email", company_name)
            if company_name:
                found = search([['name', '=ilike', company_name.strip()]])
                if found:
                    return cls._found(found[0], "name", company_name)

            partner_id = models.execute_kw(cfg['db'], uid, cfg['password'], 'res.partner', 'create', [{
                'name': company_name, 'email': contact_email, 'phone': phone, 'street': address or '',
                'website': website or '', 'vat': vat or '', 'is_company': True,
            }])
            logger.info(f"Odoo'da yeni müşteri açıldı (ID: {partner_id}, Firma: {company_name})")
            return {"id": partner_id, "name": company_name, "matched_by": "created"}
        except Exception as e:
            logger.error(f"Odoo res.partner işlemi sırasında hata: {e}")
            return None

    @staticmethod
    def _found(p: Dict[str, Any], how: str, wanted: str) -> Dict[str, Any]:
        logger.info(f"Odoo'da mevcut müşteri kullanıldı ({how}): ID={p['id']} '{p['name']}' (aranan: {wanted})")
        return {"id": p["id"], "name": p["name"], "matched_by": how}

    @classmethod
    def list_products(cls, search: Optional[str] = None, product_ids: Optional[list] = None, limit: int = 200) -> list:
        """
        Odoo'da satılabilir (sale_ok) ürün varyantları (product.product). Satış siparişi satırı bu
        ID ile açıldığı için paketlerin odoo_product_id alanı bu listeden seçilir.
        Bağlantı kurulamazsa OdooUnavailable fırlatır.
        """
        uid, models, cfg = cls._get_connection()
        if not uid or not models:
            raise OdooUnavailable("Odoo bağlantısı kurulamadı.")
        domain: list = [("sale_ok", "=", True)]
        if product_ids:
            domain.append(("id", "in", [int(i) for i in product_ids]))
        if search:
            domain += ["|", ("name", "ilike", search), ("default_code", "ilike", search)]
        try:
            rows = models.execute_kw(cfg["db"], uid, cfg["password"], "product.product", "search_read", [domain], {
                "fields": ["id", "display_name", "default_code", "list_price", "currency_id", "type"],
                "limit": limit, "order": "name",
            })
        except Exception as e:
            logger.error(f"Odoo ürün listesi alınamadı: {e}")
            raise OdooUnavailable("Odoo ürün listesi alınamadı.") from e
        return [{
            "id": r["id"], "name": r["display_name"], "code": r.get("default_code") or None,
            "list_price": r.get("list_price") or 0, "currency": (r.get("currency_id") or [None, None])[1], "type": r.get("type"),
        } for r in rows]

    @classmethod
    def create_sale_order(cls, partner_id: int, product_id: int, price: float, description: str,
                          extra_lines: Optional[list] = None) -> Dict[str, Any]:
        """
        Odoo sale.order (teklif) oluşturur. Ürün ve fiyat RECOrion paket tanımından gelir
        (plans.odoo_product_id, plans.monthly_price). extra_lines: RECDx uygulamaları (ADIM 13.1)
        [{"product_id", "price", "name"}] — paketin teklifine göre indirimli veya 0 fiyatlı satırlar.
        """
        from app.config import settings

        uid, models, cfg = cls._get_connection()
        if not uid or not models:
            return {"success": False, "error": "Odoo bağlantısı kurulamadı"}

        try:
            order_data = {
                'partner_id': partner_id,
                'partner_invoice_id': partner_id,
                'partner_shipping_id': partner_id,
                'validity_date': date.today().isoformat(),
                'date_order': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'pricelist_id': settings.ODOO_PRICELIST_ID,
                'order_line': [
                    (0, 0, {
                        'product_id': product_id,
                        'product_uom_qty': 1.0,
                        'price_unit': float(price),
                        'name': description,
                    })
                ] + [(0, 0, {'product_id': int(ln['product_id']), 'product_uom_qty': 1.0, 'price_unit': float(ln['price']),
                             'name': ln['name']}) for ln in (extra_lines or [])]
            }
            order_id = models.execute_kw(cfg['db'], uid, cfg['password'], 'sale.order', 'create', [order_data])
            orders = models.execute_kw(cfg['db'], uid, cfg['password'], 'sale.order', 'read', [[order_id]],
                                       {'fields': ['name', 'state', 'amount_total']})
            order_name = orders[0].get('name', f"SO-{order_id}") if orders else f"SO-{order_id}"
            logger.info(f"Odoo sale.order oluşturuldu: ID={order_id}, Ref={order_name}")
            return {"success": True, "order_id": order_id, "order_name": order_name, "partner_id": partner_id}
        except Exception as e:
            logger.error(f"Odoo sale.order oluşturulurken hata: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def create_quotation(cls, partner_id: int, lines: list, note: str) -> Dict[str, Any]:
        """Paket dışında ek ürünler için yeni teklif (ADIM 13.1: Şirket Yönetimi'nden 'paketime ekle')."""
        from app.config import settings

        uid, models, cfg = cls._get_connection()
        if not uid or not models:
            return {"success": False, "error": "Odoo bağlantısı kurulamadı"}
        try:
            order_id = models.execute_kw(cfg['db'], uid, cfg['password'], 'sale.order', 'create', [{
                'partner_id': partner_id, 'partner_invoice_id': partner_id, 'partner_shipping_id': partner_id,
                'pricelist_id': settings.ODOO_PRICELIST_ID, 'client_order_ref': note[:100],
                'order_line': [(0, 0, {'product_id': int(ln['product_id']), 'product_uom_qty': 1.0, 'price_unit': float(ln['price']),
                                       'name': ln['name']}) for ln in lines]}])
            name = models.execute_kw(cfg['db'], uid, cfg['password'], 'sale.order', 'read', [[order_id]], {'fields': ['name']})[0]['name']
            return {"success": True, "order_id": order_id, "order_name": name}
        except Exception as e:
            logger.error(f"Odoo ek teklif oluşturulamadı: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def create_crm_lead(cls, partner_id: Optional[int], name: str, description: str, expected_revenue: float,
                        email: Optional[str], phone: Optional[str]) -> Dict[str, Any]:
        """Odoo CRM fırsatı (ADIM 13.1: RECDx uygulaması için 'teklif istiyorum')."""
        uid, models, cfg = cls._get_connection()
        if not uid or not models:
            return {"success": False, "error": "Odoo bağlantısı kurulamadı"}
        try:
            vals = {'name': name[:255], 'type': 'opportunity', 'description': description, 'expected_revenue': float(expected_revenue or 0),
                    'email_from': email or False, 'phone': phone or False}
            if partner_id:
                vals['partner_id'] = partner_id
            lead_id = models.execute_kw(cfg['db'], uid, cfg['password'], 'crm.lead', 'create', [vals])
            return {"success": True, "lead_id": lead_id}
        except Exception as e:
            logger.error(f"Odoo CRM fırsatı oluşturulamadı: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def cancel_sale_order(cls, order_id: int) -> bool:
        """Reddedilen başvurunun Odoo siparişini iptal eder (action_cancel)."""
        uid, models, cfg = cls._get_connection()
        if not uid or not models:
            return False
        try:
            models.execute_kw(cfg['db'], uid, cfg['password'], 'sale.order', 'action_cancel', [[order_id]])
            logger.info(f"Odoo siparişi iptal edildi: Order ID={order_id}")
            return True
        except Exception as e:
            logger.warning(f"Odoo sipariş iptali (action_cancel) uyarısı: {e}")
            return False

    @classmethod
    def confirm_sale_order(cls, order_id: int) -> bool:
        """
        Ödeme onaylandığında Odoo siparişini onaylar (action_confirm).
        """
        uid, models, cfg = cls._get_connection()
        if not uid or not models:
            return False

        try:
            models.execute_kw(
                cfg['db'], uid, cfg['password'],
                'sale.order', 'action_confirm',
                [[order_id]]
            )
            logger.info(f"Odoo siparişi onaylandı: Order ID={order_id}")
            return True
        except Exception as e:
            logger.warning(f"Odoo sipariş onaylama (action_confirm) uyarısı: {e}")
            return False


_LEGAL_WORDS = {"as", "a", "s", "ltd", "sti", "şti", "tic", "san", "ve", "limited", "sirketi", "şirketi", "anonim", "the", "inc", "co"}


def _name_words(name: str) -> list:
    """Firma adının anlamlı kelimeleri (Türkçe karakterler sadeleştirilir, şirket türü ekleri atılır)."""
    tr = str.maketrans("çğıöşüâîİI", "cgiosuaiii")
    words = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower().translate(tr)).split()
    return [w for w in words if w not in _LEGAL_WORDS and len(w) > 1]


def partner_matches(company_name: str, contact_email: str, partner: Dict[str, Any]) -> bool:
    """Odoo kaydı bu şirkete mi ait: e-posta alan adı aynı veya firma adları örtüşüyor."""
    want_domain = (contact_email or "").split("@")[-1].lower()
    have_domain = (partner.get("email") or "").split("@")[-1].lower()
    if want_domain and want_domain == have_domain:
        return True
    a, b = _name_words(company_name), _name_words(partner.get("name") or "")
    if not a or not b:
        return False
    overlap = len(set(a) & set(b)) / min(len(set(a)), len(set(b)))
    joined_a, joined_b = "".join(a), "".join(b)  # "SIRIUSMES" ile "SIRIUS MES" eşleşsin
    return overlap >= 0.5 or joined_a in joined_b or joined_b in joined_a
