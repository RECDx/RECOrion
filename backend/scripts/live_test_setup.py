"""
Canlı uçtan uca test şirketi (e2e/). Tekrar çalıştırılabilir: şirket ve kullanıcılar yoksa oluşturulur, varsa
kullanıcı şifreleri her çalıştırmada yenilenir.

Kullanım (e2e/live_e2e.mjs otomatik çağırır):
    docker exec -w /app recorion_backend python scripts/live_test_setup.py
Çıktı: tek satır JSON (kullanıcılar ve geçici şifreler). Şifreler dosyaya yazılmaz; test süreci bellekte tutar.
Gerçek müşteri şirketlerine dokunmaz; yalnızca "recorion_canli_test" şirketini kullanır.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import asyncio
import json
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Actor, Department, LLMModel, Plan, Tenant
from app.db.session import AsyncSessionLocal

SLUG = "recorion_canli_test"
DOMAIN = "canli-test.recorion.example"


async def main():
    async with AsyncSessionLocal() as db:
        plan = (await db.execute(select(Plan).where(Plan.code == "PRO"))).scalar_one()
        tenant = (await db.execute(select(Tenant).where(Tenant.slug == SLUG))).scalar_one_or_none()
        if not tenant:
            tenant = Tenant(slug=SLUG, name="RECOrion Canlı Test A.Ş.", plan_id=plan.id, is_active=True,
                            contact_email=f"yonetici@{DOMAIN}")
            db.add(tenant)
            await db.flush()
        tenant.is_active = True
        tenant.package_expiry_date = datetime.now(timezone.utc) + timedelta(days=365)
        dept = (await db.execute(select(Department).where(Department.tenant_id == tenant.id, Department.name == "Bilgi Teknolojileri"))).scalar_one_or_none()
        if not dept:
            dept = Department(tenant_id=tenant.id, name="Bilgi Teknolojileri", description="Canlı test departmanı")
            db.add(dept)
            await db.flush()
        out = {"tenant_id": str(tenant.id), "users": {}}
        for key, name, role in (("manager", "Canlı Test Yöneticisi", "PROJECT_MANAGER"), ("member", "Canlı Test Uzmanı", "USER"),
                                ("outsider", "Canlı Test Dışarıdan", "USER")):
            email = f"{key}@{DOMAIN}"
            pwd = "Ct-" + secrets.token_urlsafe(12)
            a = (await db.execute(select(Actor).where(Actor.email == email))).scalar_one_or_none()
            if not a:
                a = Actor(tenant_id=tenant.id, actor_type="HUMAN", display_name=name, email=email, role=role, status="IDLE")
                db.add(a)
            a.password_hash, a.status, a.department_id = hash_password(pwd), "IDLE", dept.id
            # Test adresleri gerçek değil (.example): e-posta bildirimi kapalı, geri dönen e-posta oluşmasın
            a.notification_prefs = {"email": False, "telegram": True}
            await db.flush()
            out["users"][key] = {"id": str(a.id), "email": email, "password": pwd}
        # Deniz: mimo-v2.6-pro (EVREN'de yoğun; yedek model mekanizmasını gerçek ortamda sınar)
        # Kaan: AI personel varsayılan modeli deepseek-v4-flash
        for name, title, code in (("Deniz", "İş Analisti", "mimo-v2.6-pro"), ("Kaan", "Yazılım Geliştirici", "deepseek-v4-flash")):
            model = (await db.execute(select(LLMModel).where(LLMModel.model_code == code))).scalar_one()
            a = (await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.display_name == name))).scalar_one_or_none()
            if not a:
                a = Actor(tenant_id=tenant.id, actor_type="AI_AGENT", display_name=name, role=title, status="IDLE",
                          department_id=dept.id, autonomy_level="L2")
                db.add(a)
            a.preferred_model_id = model.id
        await db.commit()
        print(json.dumps(out))


asyncio.run(main())
