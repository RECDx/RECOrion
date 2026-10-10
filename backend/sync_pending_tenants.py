import asyncio
import re
import uuid
from datetime import datetime
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Tenant, TenantLead, Actor

async def sync():
    async with AsyncSessionLocal() as db:
        # 1. Bekleyen (PENDING) lead'leri getir
        pending_leads_res = await db.execute(select(TenantLead).where(TenantLead.status == "PENDING"))
        pending_leads = pending_leads_res.scalars().all()
        print(f"Bulunan PENDING lead sayısı: {len(pending_leads)}")

        # 2. Mevcut tenant'ları getir
        tenants_res = await db.execute(select(Tenant))
        existing_tenants = tenants_res.scalars().all()
        print(f"Mevcut Tenant sayısı: {len(existing_tenants)}")
        existing_slugs = {t.slug for t in existing_tenants}

        created_count = 0
        for lead in pending_leads:
            lead_slug_part = str(lead.id)[:6]
            has_tenant = any(lead_slug_part in t.slug for t in existing_tenants)
            if not has_tenant:
                clean_slug = re.sub(r'[^a-zA-Z0-9]', '', lead.company_name.lower())[:16] or "tenant"
                slug_candidate = f"{clean_slug}_{lead_slug_part}"
                if slug_candidate in existing_slugs:
                    slug_candidate = f"{clean_slug}_{str(uuid.uuid4())[:6]}"

                print(f"Yeni unapproved tenant ekleniyor: {lead.company_name} (Slug: {slug_candidate})")
                new_t = Tenant(
                    slug=slug_candidate,
                    name=lead.company_name,
                    tax_id=lead.tax_id,
                    tax_office=lead.tax_office,
                    phone=lead.phone,
                    address=lead.address,
                    website=lead.website,
                    contact_email=lead.contact_email,
                    plan_id=lead.plan_id,
                    nace_codes=lead.nace_codes or [],
                    sector_manifesto=lead.generated_manifesto,
                    package_start_date=None,
                    package_expiry_date=None,
                    is_active=False
                )
                db.add(new_t)
                await db.flush()

                # Şirket yöneticisi (INACTIVE) aktörü de oluştur
                contact_name = "Şirket Yöneticisi"
                pw_hash = None
                if lead.notes:
                    for part in lead.notes.split("|"):
                        if "Yetkili:" in part:
                            contact_name = part.replace("Yetkili:", "").strip()
                        if "PasswordHash:" in part:
                            pw_hash = part.replace("PasswordHash:", "").strip()

                admin_actor = Actor(
                    tenant_id=new_t.id,
                    actor_type="HUMAN",
                    display_name=f"{contact_name} (Yönetici)",
                    email=lead.contact_email,
                    phone=lead.phone,
                    address=lead.address,
                    role="COMPANY_ADMIN",
                    password_hash=pw_hash,
                    autonomy_level="L3",
                    status="DISABLED"
                )
                db.add(admin_actor)
                existing_slugs.add(slug_candidate)
                existing_tenants.append(new_t)
                created_count += 1

        if created_count > 0:
            await db.commit()
            print(f"Toplam {created_count} adet onay bekleyen şirket Tenant tablosuna eklendi.")
        else:
            print("Tüm bekleyen lead'ler zaten Tenant tablosunda mevcut.")

        # Son durum
        final_tenants = (await db.execute(select(Tenant))).scalars().all()
        print(f"Güncel Toplam Tenant Sayısı: {len(final_tenants)}")
        active_t = [t for t in final_tenants if t.is_active]
        inactive_t = [t for t in final_tenants if not t.is_active]
        print(f"Aktif / Onaylı Tenant: {len(active_t)}")
        print(f"Onay Bekleyen Tenant: {len(inactive_t)}")

if __name__ == "__main__":
    asyncio.run(sync())
