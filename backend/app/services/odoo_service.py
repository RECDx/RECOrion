import os
import xmlrpc.client
import logging
from datetime import date, datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("recorion_odoo")

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
    ) -> Optional[int]:
        """
        Odoo 19 res.partner modülünde müşteri arar. Yoksa yeni müşteri kaydı açar.
        """
        uid, models, cfg = cls._get_connection()
        if not uid or not models:
            return None

        try:
            # 1. Önce Vergi No veya E-posta veya İsim ile ara
            search_domain = []
            if tax_id:
                search_domain = [['vat', '=', tax_id]]
            elif contact_email:
                search_domain = [['email', '=', contact_email]]
            else:
                search_domain = [['name', '=', company_name]]

            partner_ids = models.execute_kw(
                cfg['db'], uid, cfg['password'],
                'res.partner', 'search',
                [search_domain]
            )

            if partner_ids:
                logger.info(f"Odoo'da mevcut müşteri bulundu (ID: {partner_ids[0]})")
                return partner_ids[0]

            # 2. Yoksa yeni partner oluştur
            partner_data = {
                'name': company_name,
                'email': contact_email,
                'phone': phone,
                'street': address or '',
                'website': website or '',
                'vat': tax_id or '',
                'is_company': True
            }

            partner_id = models.execute_kw(
                cfg['db'], uid, cfg['password'],
                'res.partner', 'create',
                [partner_data]
            )
            logger.info(f"Odoo'da yeni müşteri açıldı (ID: {partner_id}, Firma: {company_name})")
            return partner_id

        except Exception as e:
            logger.error(f"Odoo res.partner işlemi sırasında hata: {e}")
            return None

    @classmethod
    def create_sale_order(cls, partner_id: int, product_id: int, price: float, description: str) -> Dict[str, Any]:
        """
        Odoo sale.order (teklif) oluşturur. Ürün ve fiyat RECOrion paket tanımından gelir
        (plans.odoo_product_id, plans.monthly_price).
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
                ]
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
