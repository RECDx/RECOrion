"""
AI personel işe alım akışı (ADIM 5.3, Odoo #240/#272):
Sektör (şirket tanımından) > Departman > Unvan > LLM > Rol promptu.

Katalogdan seçilen departman ve unvan işe alım anında şirkete kopyalanır (departments.catalog_department_id,
job_titles.source_title_id). Böylece şirket unvanı kendi bilgi katmanını (Şirket Unvan Bilgisi) taşıyabilir;
platform kataloğundaki sonraki değişiklikler şirketin unvanını bozmaz.
"""
import uuid
from typing import Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CatalogDepartment, Department, JobTitle, Tenant

PLACEHOLDERS = ("{{company_name}}", "{{department_name}}")


def render_role_prompt(prompt: str, company_name: str, department_name: Optional[str]) -> str:
    return (prompt or "").replace("{{company_name}}", company_name or "şirket") \
        .replace("{{department_name}}", department_name or "ilgili")


def title_fits_tenant(title: JobTitle, tenant: Tenant) -> bool:
    """Genel unvanlar her şirkete; sektör unvanları şirketin sektörüne ve (tanımlıysa) meslek grubuna uyar."""
    if not title.sector_code:
        return True
    if title.sector_code not in [str(s) for s in (tenant.sectors or [])]:
        return False
    professions = {str(p) for p in (tenant.professions or [])}
    return not title.profession_codes or not professions or bool(professions & set(title.profession_codes))


async def company_department_for_catalog(db: AsyncSession, tenant: Tenant, catalog_dept: CatalogDepartment) -> Department:
    """Katalog departmanının şirketteki karşılığı; yoksa (aynı adlı departman varsa ona bağlanarak) oluşturulur."""
    dept = (await db.execute(select(Department).where(
        Department.tenant_id == tenant.id, Department.catalog_department_id == catalog_dept.id))).scalars().first()
    if dept:
        return dept
    dept = (await db.execute(select(Department).where(
        Department.tenant_id == tenant.id, func.lower(Department.name) == catalog_dept.name.lower()))).scalars().first()
    if dept:
        dept.catalog_department_id = catalog_dept.id
        return dept
    dept = Department(tenant_id=tenant.id, name=catalog_dept.name, description=catalog_dept.description,
                      catalog_department_id=catalog_dept.id)
    db.add(dept)
    await db.flush()
    return dept


async def adopt_catalog_title(db: AsyncSession, tenant: Tenant, catalog_title: JobTitle, department: Optional[Department]) -> JobTitle:
    """Katalog unvanının şirket kopyası (yoksa oluşturulur)."""
    existing = (await db.execute(select(JobTitle).where(
        JobTitle.tenant_id == tenant.id, JobTitle.source_title_id == catalog_title.id))).scalars().first()
    if existing:
        if department and not existing.department_id:
            existing.department_id = department.id
        return existing
    title = JobTitle(
        tenant_id=tenant.id, department_id=department.id if department else None, code=catalog_title.code,
        title=catalog_title.title, category=catalog_title.category, description=catalog_title.description,
        base_role_prompt=catalog_title.base_role_prompt, required_skills=catalog_title.required_skills or [],
        responsibilities=catalog_title.responsibilities or [], kpis=catalog_title.kpis or [],
        seniority=catalog_title.seniority, recommended_model_code=catalog_title.recommended_model_code,
        autonomy_level=catalog_title.autonomy_level or "L1", scope="COMPANY", sector_code=catalog_title.sector_code,
        profession_codes=catalog_title.profession_codes or [], source="CATALOG", source_title_id=catalog_title.id,
        catalog_department_id=catalog_title.catalog_department_id, ai_review_status="PLATFORM", is_active=True,
    )
    db.add(title)
    await db.flush()
    return title


async def resolve_hire_target(
    db: AsyncSession, tenant: Tenant, *, job_title_id: Optional[uuid.UUID], catalog_title_id: Optional[uuid.UUID],
    department_id: Optional[uuid.UUID], catalog_department_id: Optional[uuid.UUID],
) -> Tuple[JobTitle, Optional[Department]]:
    """İşe alımın şirket unvanını ve departmanını çözer; katalog seçimlerini şirkete aktarır."""
    department = None
    if department_id:
        department = await db.get(Department, department_id)
        if not department or department.tenant_id != tenant.id:
            raise HTTPException(status_code=404, detail="Seçilen departman bulunamadı.")

    source_id = catalog_title_id or job_title_id
    if not source_id:
        raise HTTPException(status_code=422, detail="Lütfen bir unvan seçin.")
    picked = await db.get(JobTitle, source_id)
    if not picked or (picked.tenant_id is not None and picked.tenant_id != tenant.id):
        raise HTTPException(status_code=404, detail="Seçilen unvan bulunamadı veya bu şirkete ait değil.")
    if picked.tenant_id is not None:
        return picked, department or (await db.get(Department, picked.department_id) if picked.department_id else None)

    # Platform kataloğundan seçim
    if not picked.is_active or not title_fits_tenant(picked, tenant):
        raise HTTPException(status_code=422, detail="Bu unvan şirketinizin sektörü veya meslek grubu için uygun değil.")
    if department is None:
        catalog_dept = await db.get(CatalogDepartment, catalog_department_id or picked.catalog_department_id) \
            if (catalog_department_id or picked.catalog_department_id) else None
        if catalog_dept:
            department = await company_department_for_catalog(db, tenant, catalog_dept)
    return await adopt_catalog_title(db, tenant, picked, department), department


async def default_agent_model(db, ent, job_title) -> Optional[str]:
    """Yeni AI personelin modeli: sistem varsayılanı (model.default.agent) pakette varsa o; yoksa unvanın önerisi; yoksa paketin ilk modeli."""
    from app.db.models import SystemSetting

    row = await db.get(SystemSetting, "model.default.agent")
    default = str(row.value).lower() if row and row.value else ""
    if default and ent.model_allowed(default):
        return default
    rec = (job_title.recommended_model_code or "").lower() if job_title else ""
    if rec and ent.model_allowed(rec):
        return rec
    return ent.allowed_models[0] if ent.allowed_models else (rec or default or None)
