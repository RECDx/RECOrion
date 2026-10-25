"""
Platform departman ve unvan kataloğu (ADIM 5.1).

Katalog "Platform Unvan Bilgisi" katmanıdır: tüm müşterilere açık, yalnızca genel mesleki bilgi.
Okuma giriş yapmış herkese açık; ekleme/düzenleme yalnızca Süper Admin'e (access_policy).
Şirketler kendi sektör ve meslek gruplarına uygun departmanları katalogdan içe aktarabilir.
"""
import re
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import CatalogDepartment, Department, JobTitle, Sector, Tenant
from app.db.session import get_db

router = APIRouter(tags=["Departman & Unvan Kataloğu"])

CODE_RE = re.compile(r"^[A-Z0-9_]{2,64}$")
SENIORITIES = {"JUNIOR", "MID", "SENIOR", "LEAD", "MANAGER"}


# ---------------------------------------------------------------- şemalar
class CatalogDepartmentIn(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)
    description: Optional[str] = None
    sector_code: Optional[str] = None  # boş: genel departman
    profession_codes: List[str] = []
    sort_order: int = 0
    is_active: bool = True


class CatalogTitleIn(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=2, max_length=128)
    catalog_department_id: uuid.UUID
    description: Optional[str] = None
    responsibilities: List[str] = []
    required_skills: List[str] = []
    kpis: List[str] = []
    seniority: Optional[str] = None
    profession_codes: List[str] = []
    recommended_model_code: Optional[str] = None
    autonomy_level: str = "L1"
    base_role_prompt: str = Field(min_length=20)
    is_active: bool = True


def _department_out(d: CatalogDepartment, title_count: int = 0) -> dict:
    return {
        "id": str(d.id), "code": d.code, "name": d.name, "description": d.description, "scope": d.scope,
        "sector_code": d.sector_code, "profession_codes": d.profession_codes or [], "sort_order": d.sort_order,
        "is_active": d.is_active, "title_count": title_count,
    }


def _title_out(t: JobTitle, full: bool = False) -> dict:
    out = {
        "id": str(t.id), "code": t.code, "title": t.title, "category": t.category, "scope": t.scope,
        "sector_code": t.sector_code, "catalog_department_id": str(t.catalog_department_id) if t.catalog_department_id else None,
        "seniority": t.seniority, "profession_codes": t.profession_codes or [], "description": t.description,
        "recommended_model_code": t.recommended_model_code, "autonomy_level": t.autonomy_level,
        "source": t.source, "is_active": t.is_active,
    }
    if full:
        out.update({"responsibilities": t.responsibilities or [], "required_skills": t.required_skills or [],
                    "kpis": t.kpis or [], "base_role_prompt": t.base_role_prompt,
                    "updated_at": t.updated_at})
    return out


def _clean_code(code: str) -> str:
    code = code.strip().upper()
    if not CODE_RE.match(code):
        raise HTTPException(status_code=422, detail="Kod yalnızca büyük harf, rakam ve alt çizgi içerebilir (2-64 karakter).")
    return code


async def _check_sector(db: AsyncSession, sector_code: Optional[str]) -> Optional[str]:
    if not sector_code:
        return None
    if not await db.get(Sector, sector_code):
        raise HTTPException(status_code=422, detail=f"'{sector_code}' sektörü bulunamadı.")
    return sector_code


# ---------------------------------------------------------------- okuma
@router.get("/catalog/summary")
async def catalog_summary(db: AsyncSession = Depends(get_db)):
    """Sektör bazında aktif departman ve unvan sayıları (genel kısım sector_code = null)."""
    depts = dict((await db.execute(select(CatalogDepartment.sector_code, func.count()).where(CatalogDepartment.is_active)
                                   .group_by(CatalogDepartment.sector_code))).all())
    titles = dict((await db.execute(select(JobTitle.sector_code, func.count()).where(
        JobTitle.tenant_id.is_(None), JobTitle.is_active).group_by(JobTitle.sector_code))).all())
    sectors = (await db.execute(select(Sector).order_by(Sector.code))).scalars().all()
    rows = [{"sector_code": None, "sector_name": "Genel", "departments": depts.get(None, 0), "titles": titles.get(None, 0)}]
    rows += [{"sector_code": s.code, "sector_name": s.name, "departments": depts.get(s.code, 0), "titles": titles.get(s.code, 0)}
             for s in sectors]
    return {"total_departments": sum(depts.values()), "total_titles": sum(titles.values()), "sectors": rows}


@router.get("/catalog/departments")
async def list_catalog_departments(
    sector_code: Optional[str] = Query(None, description="Sektör kodu; 'GENERAL' yalnızca genel departmanlar"),
    include_inactive: bool = False,
    current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    stmt = select(CatalogDepartment)
    if sector_code == "GENERAL":
        stmt = stmt.where(CatalogDepartment.sector_code.is_(None))
    elif sector_code:
        stmt = stmt.where(CatalogDepartment.sector_code == sector_code)
    if not (include_inactive and current.is_super_admin):
        stmt = stmt.where(CatalogDepartment.is_active)
    depts = (await db.execute(stmt.order_by(CatalogDepartment.sector_code.nulls_first(), CatalogDepartment.sort_order,
                                            CatalogDepartment.name))).scalars().all()
    counts = dict((await db.execute(select(JobTitle.catalog_department_id, func.count()).where(
        JobTitle.tenant_id.is_(None), JobTitle.is_active).group_by(JobTitle.catalog_department_id))).all())
    return [_department_out(d, counts.get(d.id, 0)) for d in depts]


@router.get("/catalog/titles")
async def list_catalog_titles(
    catalog_department_id: Optional[uuid.UUID] = None,
    sector_code: Optional[str] = Query(None, description="Sektör kodu; 'GENERAL' yalnızca genel unvanlar"),
    profession_code: Optional[str] = None,
    search: Optional[str] = Query(None, max_length=100),
    include_inactive: bool = False,
    limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    conds = [JobTitle.tenant_id.is_(None)]
    if catalog_department_id:
        conds.append(JobTitle.catalog_department_id == catalog_department_id)
    if sector_code == "GENERAL":
        conds.append(JobTitle.sector_code.is_(None))
    elif sector_code:
        conds.append(JobTitle.sector_code == sector_code)
    if profession_code:
        # Meslek grubuna özel unvanlar + o sektörün meslek ayrımı yapılmamış unvanları
        conds.append(or_(JobTitle.profession_codes.contains([profession_code]), JobTitle.profession_codes == []))
    if search:
        like = f"%{search.strip()}%"
        conds.append(or_(JobTitle.title.ilike(like), JobTitle.description.ilike(like), JobTitle.code.ilike(like)))
    if not (include_inactive and current.is_super_admin):
        conds.append(JobTitle.is_active)
    total = (await db.execute(select(func.count()).select_from(JobTitle).where(*conds))).scalar()
    rows = (await db.execute(select(JobTitle).where(*conds).order_by(JobTitle.sector_code.nulls_first(), JobTitle.category,
                                                                      JobTitle.title).limit(limit).offset(offset))).scalars().all()
    return {"total": total, "items": [_title_out(t) for t in rows]}


@router.get("/catalog/titles/{title_id}")
async def get_catalog_title(title_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    t = await db.get(JobTitle, title_id)
    if not t or t.tenant_id is not None:
        raise HTTPException(status_code=404, detail="Katalog unvanı bulunamadı.")
    return _title_out(t, full=True)


# ---------------------------------------------------------------- Süper Admin: düzenleme
@router.post("/catalog/departments", status_code=201)
async def create_catalog_department(payload: CatalogDepartmentIn, db: AsyncSession = Depends(get_db)):
    code = _clean_code(payload.code)
    if (await db.execute(select(CatalogDepartment.id).where(CatalogDepartment.code == code))).first():
        raise HTTPException(status_code=409, detail=f"'{code}' kodlu departman zaten var.")
    sector = await _check_sector(db, payload.sector_code)
    d = CatalogDepartment(code=code, name=payload.name.strip(), description=payload.description,
                          scope="SECTOR" if sector else "GENERAL", sector_code=sector,
                          profession_codes=payload.profession_codes, sort_order=payload.sort_order, is_active=payload.is_active)
    db.add(d)
    await db.commit()
    return _department_out(d)


@router.put("/catalog/departments/{department_id}")
async def update_catalog_department(department_id: uuid.UUID, payload: CatalogDepartmentIn, db: AsyncSession = Depends(get_db)):
    d = await db.get(CatalogDepartment, department_id)
    if not d:
        raise HTTPException(status_code=404, detail="Katalog departmanı bulunamadı.")
    code = _clean_code(payload.code)
    if code != d.code and (await db.execute(select(CatalogDepartment.id).where(CatalogDepartment.code == code))).first():
        raise HTTPException(status_code=409, detail=f"'{code}' kodlu departman zaten var.")
    d.code, d.name, d.description = code, payload.name.strip(), payload.description
    d.sector_code = await _check_sector(db, payload.sector_code)
    d.scope = "SECTOR" if d.sector_code else "GENERAL"
    d.profession_codes, d.sort_order, d.is_active = payload.profession_codes, payload.sort_order, payload.is_active
    for t in (await db.execute(select(JobTitle).where(JobTitle.catalog_department_id == d.id, JobTitle.tenant_id.is_(None)))).scalars():
        t.category = d.name
    await db.commit()
    return _department_out(d)


@router.delete("/catalog/departments/{department_id}")
async def delete_catalog_department(department_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    d = await db.get(CatalogDepartment, department_id)
    if not d:
        raise HTTPException(status_code=404, detail="Katalog departmanı bulunamadı.")
    count = (await db.execute(select(func.count()).select_from(JobTitle).where(JobTitle.catalog_department_id == d.id))).scalar()
    if count:
        raise HTTPException(status_code=409, detail=f"Bu departmanda {count} unvan var. Önce unvanları taşıyın ya da departmanı pasife alın.")
    await db.delete(d)
    await db.commit()
    return {"success": True}


async def _apply_title(db: AsyncSession, t: JobTitle, payload: CatalogTitleIn) -> None:
    dept = await db.get(CatalogDepartment, payload.catalog_department_id)
    if not dept:
        raise HTTPException(status_code=422, detail="Seçilen katalog departmanı bulunamadı.")
    if payload.seniority and payload.seniority not in SENIORITIES:
        raise HTTPException(status_code=422, detail="Geçersiz kıdem.")
    if payload.autonomy_level not in {"L1", "L2", "L3"}:
        raise HTTPException(status_code=422, detail="Geçersiz otonomi seviyesi.")
    t.title, t.catalog_department_id, t.category = payload.title.strip(), dept.id, dept.name
    t.scope, t.sector_code = dept.scope, dept.sector_code
    t.description, t.responsibilities, t.required_skills, t.kpis = payload.description, payload.responsibilities, payload.required_skills, payload.kpis
    t.seniority, t.profession_codes = payload.seniority, payload.profession_codes
    t.recommended_model_code = (payload.recommended_model_code or "").strip() or None
    t.autonomy_level, t.base_role_prompt, t.is_active = payload.autonomy_level, payload.base_role_prompt.strip(), payload.is_active
    t.updated_at = datetime.utcnow()


@router.post("/catalog/titles", status_code=201)
async def create_catalog_title(payload: CatalogTitleIn, db: AsyncSession = Depends(get_db)):
    code = _clean_code(payload.code)
    if (await db.execute(select(JobTitle.id).where(JobTitle.code == code, JobTitle.tenant_id.is_(None)))).first():
        raise HTTPException(status_code=409, detail=f"'{code}' kodlu unvan zaten var.")
    t = JobTitle(tenant_id=None, code=code, source="ADMIN", ai_review_status="PLATFORM", title="", category="", base_role_prompt="")
    await _apply_title(db, t, payload)
    db.add(t)
    await db.commit()
    return _title_out(t, full=True)


@router.put("/catalog/titles/{title_id}")
async def update_catalog_title(title_id: uuid.UUID, payload: CatalogTitleIn, db: AsyncSession = Depends(get_db)):
    t = await db.get(JobTitle, title_id)
    if not t or t.tenant_id is not None:
        raise HTTPException(status_code=404, detail="Katalog unvanı bulunamadı.")
    code = _clean_code(payload.code)
    if code != t.code and (await db.execute(select(JobTitle.id).where(JobTitle.code == code, JobTitle.tenant_id.is_(None)))).first():
        raise HTTPException(status_code=409, detail=f"'{code}' kodlu unvan zaten var.")
    t.code = code
    await _apply_title(db, t, payload)
    await db.commit()
    return _title_out(t, full=True)


@router.delete("/catalog/titles/{title_id}")
async def delete_catalog_title(title_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Şirketlerin kullandığı unvan silinmez, pasife alınır (yeni işe alımlarda görünmez)."""
    t = await db.get(JobTitle, title_id)
    if not t or t.tenant_id is not None:
        raise HTTPException(status_code=404, detail="Katalog unvanı bulunamadı.")
    used = (await db.execute(select(func.count()).select_from(JobTitle).where(JobTitle.source_title_id == t.id))).scalar()
    if used:
        t.is_active = False
        await db.commit()
        return {"success": True, "deactivated": True,
                "message": f"Unvan {used} şirkette kullanıldığı için silinmedi, pasife alındı."}
    await db.delete(t)
    await db.commit()
    return {"success": True, "deactivated": False}


# ---------------------------------------------------------------- şirket: öneri ve içe aktarma
async def _tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    return tenant


@router.get("/company/{tenant_id}/catalog/recommended")
async def recommended_for_company(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Şirketin sektör ve meslek gruplarına uygun katalog departmanları: önce meslek grubuyla eşleşen
    sektör departmanları, sonra sektörün diğer departmanları, sonra genel departmanlar.
    """
    tenant = await _tenant(db, tenant_id)
    sectors = [str(s) for s in (tenant.sectors or [])]
    professions = set(str(p) for p in (tenant.professions or []))
    depts = (await db.execute(select(CatalogDepartment).where(
        CatalogDepartment.is_active, or_(CatalogDepartment.sector_code.is_(None), CatalogDepartment.sector_code.in_(sectors or ["-"])),
    ))).scalars().all()
    titles = (await db.execute(select(JobTitle).where(
        JobTitle.tenant_id.is_(None), JobTitle.is_active, JobTitle.catalog_department_id.in_([d.id for d in depts] or [uuid.uuid4()]),
    ))).scalars().all()
    imported = {d.catalog_department_id for d in (await db.execute(select(Department).where(
        Department.tenant_id == tenant.id, Department.catalog_department_id.isnot(None)))).scalars()}

    def fits(t: JobTitle) -> bool:
        # Genel unvanlar herkese; sektör unvanları şirketin sektörüne ve (tanımlıysa) meslek grubuna uyar
        if not t.sector_code:
            return True
        if t.sector_code not in sectors:
            return False
        return not t.profession_codes or not professions or bool(professions & set(t.profession_codes))

    out = []
    for d in depts:
        dt = [t for t in titles if t.catalog_department_id == d.id and fits(t)]
        if not dt and d.sector_code:
            continue
        match = bool(professions & set(d.profession_codes or []))
        rank = 0 if (d.sector_code and match) else 1 if d.sector_code else 2
        out.append({**_department_out(d, len(dt)), "profession_match": match, "imported": d.id in imported, "rank": rank})
    out.sort(key=lambda r: (r["rank"], r["sort_order"], r["name"]))
    return {"sectors": sectors, "professions": sorted(professions), "departments": out}


class ImportDepartmentsIn(BaseModel):
    catalog_department_ids: List[uuid.UUID] = Field(min_length=1, max_length=100)


@router.post("/company/{tenant_id}/departments/from-catalog")
async def import_departments(tenant_id: uuid.UUID, payload: ImportDepartmentsIn, db: AsyncSession = Depends(get_db)):
    """Seçilen katalog departmanlarını şirket departmanı olarak ekler (aynı adlı departman varsa bağlar)."""
    tenant = await _tenant(db, tenant_id)
    existing = {d.name.lower(): d for d in (await db.execute(select(Department).where(Department.tenant_id == tenant.id))).scalars()}
    created, linked = [], []
    for cd in (await db.execute(select(CatalogDepartment).where(
            CatalogDepartment.id.in_(payload.catalog_department_ids), CatalogDepartment.is_active))).scalars():
        if cd.sector_code and cd.sector_code not in [str(s) for s in (tenant.sectors or [])]:
            continue
        current = existing.get(cd.name.lower())
        if current:
            if not current.catalog_department_id:
                current.catalog_department_id = cd.id
                linked.append(cd.name)
            continue
        dept = Department(tenant_id=tenant.id, name=cd.name, description=cd.description, catalog_department_id=cd.id)
        db.add(dept)
        existing[cd.name.lower()] = dept
        created.append(cd.name)
    await db.commit()
    return {"success": True, "created": created, "linked": linked}


# ---------------------------------------------------------------- işe alım sihirbazı (ADIM 5.3)
@router.get("/company/{tenant_id}/hire/options")
async def hire_options(tenant_id: uuid.UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Sihirbazın 1. adımı: şirketin sektörleri, seçilebilir departmanlar (şirketin kendi departmanları +
    katalogdan önerilenler), paket izinleri, kullanılabilir modeller ve AI personel kotası.
    """
    from app.db.models import Actor, LLMModel, Plan
    from app.services.llm_gateway import CHAT_TYPES
    from app.services.plan_features import entitlements

    tenant = await _tenant(db, tenant_id)
    ent = await entitlements(db, tenant, current)
    rec = await recommended_for_company(tenant_id, db)
    sectors = {s.code: s.name for s in (await db.execute(select(Sector).where(Sector.code.in_(rec["sectors"] or ["-"])))).scalars()}
    company_depts = (await db.execute(select(Department).where(Department.tenant_id == tenant.id).order_by(Department.name))).scalars().all()
    linked = {d.catalog_department_id: d for d in company_depts if d.catalog_department_id}

    departments = [{
        "key": f"company:{d.id}", "department_id": str(d.id),
        "catalog_department_id": str(d.catalog_department_id) if d.catalog_department_id else None,
        "name": d.name, "description": d.description, "source": "COMPANY", "rank": -1, "profession_match": False,
    } for d in company_depts]
    for cd in rec["departments"]:
        if uuid.UUID(cd["id"]) in linked:
            continue
        departments.append({"key": f"catalog:{cd['id']}", "department_id": None, "catalog_department_id": cd["id"],
                            "name": cd["name"], "description": cd["description"], "source": "CATALOG", "rank": cd["rank"],
                            "profession_match": cd["profession_match"], "title_count": cd["title_count"]})

    from app.services import recai

    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    tier_opts = await recai.options(db, plan, bypass=ent.bypass)
    active = (await db.execute(select(func.count(Actor.id)).where(
        Actor.tenant_id == tenant.id, Actor.actor_type == "AI_AGENT", Actor.status != "DISABLED"))).scalar() or 0
    return {
        "company_name": tenant.name,
        "sectors": [{"code": c, "name": sectors.get(c, c)} for c in rec["sectors"]],
        "professions": rec["professions"],
        "departments": departments,
        "entitlements": {"plan_name": ent.plan_name, "can_change_llm": ent.can_change_llm,
                         "can_edit_role_prompt": ent.can_edit_role_prompt},
        # #349: model yerine RECAi adları (Mergen/Hızlı/Derin) ve yetenekler (Görsel/Ses/Okur)
        "models": [o for o in tier_opts if o["available"]],
        "capabilities": await recai.capability_options(db, plan, bypass=ent.bypass),
        "quota": {"max_agents": plan.max_agents if plan else None, "active_agents": active,
                  "is_limit_reached": bool(plan and plan.max_agents is not None and active >= plan.max_agents)},
    }


@router.get("/company/{tenant_id}/hire/titles")
async def hire_titles(tenant_id: uuid.UUID, department_id: Optional[uuid.UUID] = None,
                      catalog_department_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    """
    Sihirbazın 2. adımı: seçilen departmandaki unvanlar. Şirketin kendi unvanları ve (departman katalogla
    bağlıysa) şirketin sektör/meslek grubuna uyan katalog unvanları; şirkete zaten alınmış katalog
    unvanları şirket unvanı olarak bir kez listelenir.
    """
    from app.services.hiring import title_fits_tenant

    tenant = await _tenant(db, tenant_id)
    if department_id:
        dept = await db.get(Department, department_id)
        if not dept or dept.tenant_id != tenant.id:
            raise HTTPException(status_code=404, detail="Departman bulunamadı.")
        catalog_department_id = catalog_department_id or dept.catalog_department_id
    company_titles = []
    if department_id:
        company_titles = (await db.execute(select(JobTitle).where(
            JobTitle.tenant_id == tenant.id, JobTitle.department_id == department_id, JobTitle.is_active))).scalars().all()
    adopted = {t.source_title_id: t for t in (await db.execute(select(JobTitle).where(
        JobTitle.tenant_id == tenant.id, JobTitle.source_title_id.isnot(None)))).scalars()}
    professions = {str(p) for p in (tenant.professions or [])}

    def item(t: JobTitle, kind: str) -> dict:
        return {"id": str(t.id), "kind": kind, "title": t.title, "seniority": t.seniority, "description": t.description,
                "recommended_model_code": t.recommended_tier, "autonomy_level": t.autonomy_level,
                "profession_match": bool(professions & set(t.profession_codes or []))}

    items = [item(t, "COMPANY") for t in company_titles]
    seen = {t.id for t in company_titles} | {t.source_title_id for t in company_titles if t.source_title_id}
    if catalog_department_id:
        for t in (await db.execute(select(JobTitle).where(
                JobTitle.tenant_id.is_(None), JobTitle.is_active, JobTitle.catalog_department_id == catalog_department_id))).scalars():
            if t.id in seen or not title_fits_tenant(t, tenant):
                continue
            if t.id in adopted:
                items.append(item(adopted[t.id], "COMPANY"))
            else:
                items.append(item(t, "CATALOG"))
    items.sort(key=lambda r: (r["kind"] != "COMPANY", not r["profession_match"], r["title"]))
    return items


@router.get("/company/{tenant_id}/hire/preview")
async def hire_preview(tenant_id: uuid.UUID, title_id: uuid.UUID, department_name: Optional[str] = Query(None, max_length=128),
                       current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Sihirbazın 3. adımı: unvanın şirket ve departman adıyla doldurulmuş rol promptu ve kullanılacak model."""
    from app.services.hiring import default_agent_tier, render_role_prompt
    from app.services.plan_features import entitlements

    tenant = await _tenant(db, tenant_id)
    t = await db.get(JobTitle, title_id)
    if not t or (t.tenant_id is not None and t.tenant_id != tenant.id):
        raise HTTPException(status_code=404, detail="Unvan bulunamadı.")
    ent = await entitlements(db, tenant, current)
    rec = t.recommended_tier  # #349: RECAi adı
    default = default_agent_tier(ent, t)
    return {
        "title": t.title, "description": t.description, "seniority": t.seniority, "autonomy_level": t.autonomy_level or "L1",
        "responsibilities": t.responsibilities or [], "required_skills": t.required_skills or [], "kpis": t.kpis or [],
        "role_prompt": render_role_prompt(t.base_role_prompt, tenant.name, department_name),
        "recommended_model_code": rec if rec and ent.tier_allowed(rec) else None,
        # Varsayılan: AI personel varsayılan modeli (model.default.agent); unvanın önerisi bilgi olarak gösterilir
        "model_code": default,
    }
