"""
Dashboard uçları (ADIM 9).

GET /company/{tenant_id}/dashboard?days=30&department_id=
  - Şirket yöneticisi (tenant:manage): tüm şirket veya seçtiği departman.
  - Departman panosu yetkisi (department:dashboard, ADIM 9.3): yalnızca kendi departmanı; başka departman istenemez.
  - Parasal bilgiler (TL maliyet, bütçe, tahmini tasarruf) yalnızca billing:view ile; diğerleri iş durumunu görür.
  - Platform personeli (RECDx) müşteri içeriğini göremez (KVKK).
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import Department, Tenant
from app.db.session import get_db
from app.services import dashboards, platform_health

router = APIRouter(tags=["Dashboard ve Raporlar"])


async def dashboard_scope(db: AsyncSession, user: CurrentUser, tenant_id: uuid.UUID, department_id: Optional[uuid.UUID]):
    """Kim neyi görür. Dönüş: (şirket, departman, departman adı, parasal bilgiyi görür mü)."""
    ensure_tenant_content(user, tenant_id)
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    if not user.has("tenant:manage"):
        if not user.has("department:dashboard"):
            raise forbidden("Panoyu yalnızca şirket yöneticisi veya departman panosu yetkisi olanlar görebilir.")
        own = user.actor.department_id
        if not own:
            raise forbidden("Departmanınız tanımlı değil; departman panosu için şirket yöneticinize başvurun.")
        if department_id and department_id != own:
            raise forbidden("Yalnızca kendi departmanınızın panosunu görebilirsiniz.")
        department_id = own
    dept = None
    if department_id:
        dept = await db.get(Department, department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Departman bulunamadı.")
    return tenant, department_id, dept.name if dept else None, user.has("billing:view") or user.has("tenant:manage")


@router.get("/system/dashboard")
async def platform_dashboard(days: int = Query(7), user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Süper Admin panosu (ADIM 9.4): yalnızca platform düzeyinde sayılar; müşteri içeriği yok (KVKK)."""
    if days not in dashboards.PERIODS:
        raise HTTPException(status_code=422, detail="Dönem 7, 30, 90 veya 365 gün olabilir.")
    return await dashboards.platform_overview(db, days)


@router.get("/system/health")
async def platform_health_check(refresh: bool = False, user: CurrentUser = Depends(get_current_user)):
    """Bileşenlerin gerçek durumu (30 sn önbellek; refresh=true yeniden ölçer)."""
    return await platform_health.check_all(force=refresh)


@router.get("/company/{tenant_id}/dashboard")
async def company_dashboard(tenant_id: uuid.UUID, days: int = Query(30), department_id: Optional[uuid.UUID] = None,
                            user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if days not in dashboards.PERIODS:
        raise HTTPException(status_code=422, detail="Dönem 7, 30, 90 veya 365 gün olabilir.")
    tenant, dept, dept_name, money = await dashboard_scope(db, user, tenant_id, department_id)
    out = await dashboards.company_overview(db, tenant, days, dept)
    out["department_name"] = dept_name
    out["department_locked"] = not user.has("tenant:manage")
    out["can_view_costs"] = money
    return out if money else dashboards.without_money(out)
