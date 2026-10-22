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
            await db.flush()
            out["users"][key] = {"id": str(a.id), "email": email, "password": pwd}
        model = (await db.execute(select(LLMModel).where(LLMModel.model_code == "mimo-v2.6-pro"))).scalar_one()
        for name, title in (("Deniz", "İş Analisti"), ("Kaan", "Yazılım Geliştirici")):
            a = (await db.execute(select(Actor).where(Actor.tenant_id == tenant.id, Actor.display_name == name))).scalar_one_or_none()
            if not a:
                a = Actor(tenant_id=tenant.id, actor_type="AI_AGENT", display_name=name, role=title, status="IDLE",
                          preferred_model_id=model.id, department_id=dept.id, autonomy_level="L2")
                db.add(a)
        await db.commit()
        print(json.dumps(out))


asyncio.run(main())
