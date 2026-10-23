"""
Dashboard uçları (ADIM 9).

GET /company/{tenant_id}/dashboard?days=30&department_id=
  Şirket yöneticisi (tenant:manage) tüm şirketi veya bir departmanı görür. Platform personeli (RECDx) müşteri içeriğini
  göremez (KVKK). Departman görünümü kuralları ADIM 9.3'te genişletilir.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, ensure_tenant_content, forbidden, get_current_user
from app.db.models import Department, Tenant
from app.db.session import get_db
from app.services import dashboards

router = APIRouter(tags=["Dashboard ve Raporlar"])


async def dashboard_scope(db: AsyncSession, user: CurrentUser, tenant_id: uuid.UUID, department_id: Optional[uuid.UUID]):
    """Kim neyi görür: şirket yöneticisi tümünü (isterse bir departmanı)."""
    ensure_tenant_content(user, tenant_id)
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    if department_id:
        dept = await db.get(Department, department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Departman bulunamadı.")
    if not user.has("tenant:manage"):
        raise forbidden("Şirket panosunu yalnızca şirket yöneticisi görebilir.")
    return tenant, department_id


@router.get("/company/{tenant_id}/dashboard")
async def company_dashboard(tenant_id: uuid.UUID, days: int = Query(30), department_id: Optional[uuid.UUID] = None,
                            user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if days not in dashboards.PERIODS:
        raise HTTPException(status_code=422, detail="Dönem 7, 30, 90 veya 365 gün olabilir.")
    tenant, dept = await dashboard_scope(db, user, tenant_id, department_id)
    return await dashboards.company_overview(db, tenant, days, dept)
