"""
Müşteri Şirket Yönetimi (Company Admin) API'leri.

Bu modül, şirketin kendi yöneticisinin (COMPANY_ADMIN) kullandığı ekranların
arka uç uçlarını barındırır: Departmanlar, Ünvanlar ve AI Ajan işe alım.
Tüm uçlar `tenant_id` ile kapsamlandırılmıştır; bir şirket yalnızca kendi verisini görür.
"""
import asyncio
import io
import json
import logging
import os
import re
import shutil
from datetime import datetime
from typing import List, Optional, Any, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
import httpx
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import (
    Department, Tenant, Actor, JobTitle, SystemSetting, LLMModel,
    Plan, TenantRole, SystemPermission, AgentDocument, MemoryItem
)
from app.api.v1.auth import hash_password
from app.core.net import UnsafeURLError, safe_request
from app.core.security import CurrentUser, forbidden, get_current_user
from app.services.plan_features import deny, ensure_document_quota, entitlements

logger = logging.getLogger(__name__)

from app.services import recai  # noqa: E402  (#349)

router = APIRouter(prefix="/company", tags=["Şirket Yönetimi (Company Admin)"])


# ------------------------------------------------------------------
# Ortak yardımcılar
# ------------------------------------------------------------------
async def _get_tenant_or_404(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    return tenant


# ==================================================================
# MADDE 1: DEPARTMANLAR
# ==================================================================
class DepartmentIn(BaseModel):
    name: str = Field(..., description="Departman Adı")
    description: Optional[str] = Field(None, description="Departman Açıklaması")


class DepartmentOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    actor_count: int = 0

    class Config:
        from_attributes = True


def _clean_department_payload(payload: DepartmentIn) -> tuple[str, Optional[str]]:
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Departman adı boş bırakılamaz.")
    if len(name) > 128:
        raise HTTPException(status_code=422, detail="Departman adı en fazla 128 karakter olabilir.")
    description = (payload.description or "").strip() or None
    return name, description


async def _assert_department_name_free(
    db: AsyncSession, tenant_id: uuid.UUID, name: str, exclude_id: Optional[uuid.UUID] = None
) -> None:
    stmt = select(Department.id).where(
        Department.tenant_id == tenant_id,
        func.lower(Department.name) == name.lower(),
    )
    if exclude_id:
        stmt = stmt.where(Department.id != exclude_id)
    exists = (await db.execute(stmt)).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"'{name}' adında bir departman zaten tanımlı.")


async def _get_department_or_404(db: AsyncSession, tenant_id: uuid.UUID, department_id: uuid.UUID) -> Department:
    dept = await db.get(Department, department_id)
    # Başka bir şirketin departmanına erişimi engelle (tenant izolasyonu)
    if not dept or dept.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Departman bulunamadı.")
    return dept


@router.get("/{tenant_id}/departments", response_model=List[DepartmentOut])
async def list_departments(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Şirketin tüm departmanlarını (ada göre sıralı) ve personel sayılarını listeler."""
    await _get_tenant_or_404(db, tenant_id)
    result = await db.execute(
        select(Department).where(Department.tenant_id == tenant_id).order_by(func.lower(Department.name))
    )
    depts = result.scalars().all()

    # Departman bazında personel sayısını çek
    counts_query = await db.execute(
        select(Actor.department_id, func.count(Actor.id))
        .where(Actor.tenant_id == tenant_id, Actor.department_id != None)
        .group_by(Actor.department_id)
    )
    counts_map = dict(counts_query.all())

    out = []
    for d in depts:
        item = DepartmentOut.model_validate(d)
        item.actor_count = counts_map.get(d.id, 0)
        out.append(item)
    return out


@router.post("/{tenant_id}/departments", response_model=DepartmentOut, status_code=201)
async def create_department(tenant_id: uuid.UUID, payload: DepartmentIn, db: AsyncSession = Depends(get_db)):
    """Yeni departman tanımlar (Departman Adı + Açıklama)."""
    await _get_tenant_or_404(db, tenant_id)
    name, description = _clean_department_payload(payload)
    await _assert_department_name_free(db, tenant_id, name)

    dept = Department(tenant_id=tenant_id, name=name, description=description)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.put("/{tenant_id}/departments/{department_id}", response_model=DepartmentOut)
async def update_department(
    tenant_id: uuid.UUID, department_id: uuid.UUID, payload: DepartmentIn, db: AsyncSession = Depends(get_db)
):
    """Departman adı ve açıklamasını günceller."""
    dept = await _get_department_or_404(db, tenant_id, department_id)
    name, description = _clean_department_payload(payload)
    await _assert_department_name_free(db, tenant_id, name, exclude_id=department_id)

    dept.name = name
    dept.description = description
    await db.commit()
    await db.refresh(dept)
    return dept


@router.delete("/{tenant_id}/departments/{department_id}")
async def delete_department(tenant_id: uuid.UUID, department_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Departmanı siler."""
    dept = await _get_department_or_404(db, tenant_id, department_id)
    name = dept.name
    await db.delete(dept)
    await db.commit()
    return {"success": True, "message": f"'{name}' departmanı silindi."}


# ==================================================================
# MADDE 2: ŞİRKET ÜNVANLARI VE RECAi KONTROL MOTORU
# ==================================================================
class CompanyJobTitleIn(BaseModel):
    title: str = Field(..., description="Ünvan Adı")
    code: Optional[str] = Field(None, description="Ünvan Kodu (Boş ise otomatik üretilir)")
    category: str = Field("GENEL", description="Kategori / Sektör")
    department_id: Optional[uuid.UUID] = Field(None, description="Bağlı Departman")
    description: Optional[str] = Field(None, description="Ünvan Açıklaması")
    base_role_prompt: str = Field(..., description="Sistem Rol Promptu")
    required_skills: List[str] = Field(default_factory=list, description="Gerekli Yetenekler")
    recommended_model_code: Optional[str] = Field(None, description="Önerilen RECAi adı (MERGEN, HIZLI, DERIN)")
    autonomy_level: str = Field("L1", description="Otonomi Seviyesi (L1, L2, L3)")
    source_template_id: Optional[uuid.UUID] = Field(None, description="Seçilen Sistem Şablonu ID'si")


class CompanyJobTitleOut(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    code: str
    title: str
    category: str
    description: Optional[str] = None
    base_role_prompt: str
    required_skills: List[str] = []
    recommended_model_code: Optional[str] = Field(None, validation_alias=AliasChoices("recommended_tier", "recommended_model_code"))  # #349: RECAi adı
    autonomy_level: str = "L1"
    ai_review_status: Optional[str] = "COMPANY_LOCAL"
    ai_review_feedback: Optional[str] = None
    is_active: bool = True
    actor_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemJobTitleTemplateOut(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    category: str
    description: Optional[str] = None
    base_role_prompt: str
    required_skills: List[str] = []
    recommended_model_code: Optional[str] = Field(None, validation_alias=AliasChoices("recommended_tier", "recommended_model_code"))  # #349: RECAi adı
    autonomy_level: str = "L1"
    is_nace_recommended: bool = False
    is_sector_recommended: bool = False

    class Config:
        from_attributes = True


def _slugify_code(text: str) -> str:
    """Türkçe ve özel karakterleri temizleyip UPPERCASE kod üretir."""
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    cleaned = text.translate(tr_map).upper()
    cleaned = re.sub(r"[^A-Z0-9]+", "_", cleaned).strip("_")
    return cleaned[:60] or "UNVAN"


async def _evaluate_job_title_with_ai(
    title: str,
    category: str,
    description: Optional[str],
    role_prompt: str,
    db: AsyncSession
) -> tuple[bool, int, str]:
    """
    RECAi her yeni tanımlanan unvanları kontrol eder (Madde 2).
    Sistemin geneli için faydalı olarak gördüğü Ünvanları Ana şablona ekler.
    """
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext, LLMError


    eval_instruction = f"""Sen RECOrion Otonom Kurumsal Yapay Zeka Fabrikasının Baş Mimarı ve Kolektif Bilgi İnceleme Motorusun.
Bir şirket kendi organizasyonu için yeni bir dijital personel ünvanı ve Sistem Rol Promptu tanımladı:

Ünvan: {title}
Kategori / Sektör: {category}
Açıklama: {description or 'Yok'}
Rol Promptu:
{role_prompt}

GÖREVİN:
Bu ünvan ve rol promptunu dikkatlice incele:
1. Şirkete özel ticari sır, özel kişi adı veya spesifik firma ismi içeriyor mu? (İçermiyorsa temizdir)
2. Bu ünvan ve prompt, RECOrion ekosistemindeki diğer şirketler ve genel pazar için faydalı, yüksek kaliteli, tekrar kullanılabilir bir kurumsal şablon mu?
3. 1 ile 100 arasında bir Genel Fayda Puanı (utility score) belirle. Eğer puan >= 75 ise 'is_beneficial': true olmalıdır.

Yanıtını YALNIZCA geçerli bir JSON objesi olarak ver:
{{"score": 88, "is_beneficial": true, "reason": "Sektörel standartlara uygun, temiz ve tekrar kullanılabilir mimari prompt"}}"""

    try:
        result = await llm_gateway.chat(
            LLMContext(tenant_id=None, purpose="TITLE_REVIEW"),  # platform (RECDx) maliyeti
            [
                {"role": "system", "content": "Sen geçerli bir JSON objesi üreten deterministik bir AI denetim motorusun."},
                {"role": "user", "content": eval_instruction},
            ],
            temperature=0.3, max_tokens=1024, timeout=60,
        )
        clean_json = result.content.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()

        parsed = json.loads(clean_json)
        score = int(parsed.get("score", 0))
        is_beneficial = bool(parsed.get("is_beneficial", score >= 75))
        reason = str(parsed.get("reason", "İncelendi.")).strip()
        return is_beneficial, score, reason
    except (LLMError, ValueError, KeyError) as e:
        # Önceden basit bir kurala göre "faydalı" sayılıp global şablona eklenebiliyordu.
        # AI incelemesi yapılamazsa ünvan şirkete özel kalır; RECDx daha sonra inceleyebilir.
        logger.warning(f"Ünvan AI incelemesi yapılamadı: {e}")
        return False, 0, "AI incelemesi yapılamadı; ünvan şirkete özel olarak kaydedildi."


@router.get("/{tenant_id}/job-titles/system-templates", response_model=List[SystemJobTitleTemplateOut])
async def list_system_job_title_templates(
    tenant_id: uuid.UUID,
    category: Optional[str] = Query(None, description="Kategori filtresi"),
    search: Optional[str] = Query(None, description="Arama metni"),
    db: AsyncSession = Depends(get_db)
):
    """
    Süper Yönetim Konsolunda tanımlı olan genel sistem ünvanlarını listeler.
    Şirketin NACE koduna uygun olanları 'is_nace_recommended' olarak etiketler.
    """
    tenant = await _get_tenant_or_404(db, tenant_id)

    stmt = select(JobTitle).where(JobTitle.tenant_id == None, JobTitle.is_active == True)
    if category:
        stmt = stmt.where(func.upper(JobTitle.category) == category.upper())
    stmt = stmt.order_by(JobTitle.category, JobTitle.title)

    templates = (await db.execute(stmt)).scalars().all()

    # Şirketin tanımlı sektörlerini incele (Madde 2)
    company_sectors = [str(s).upper().strip() for s in (tenant.sectors or []) if s]

    # Şirketin NACE kodlarını incele
    nace_keywords = []
    if tenant.nace_codes:
        for n in tenant.nace_codes:
            if isinstance(n, dict):
                nace_keywords.append((n.get("code") or "").lower())
                nace_keywords.append((n.get("title") or "").lower())
                nace_keywords.append((n.get("sector_group") or "").lower())
            elif isinstance(n, str):
                nace_keywords.append(n.lower())

    nace_joined = " ".join(nace_keywords)

    out = []
    search_q = (search or "").lower().strip()
    for t in templates:
        if search_q:
            if search_q not in t.title.lower() and search_q not in (t.description or "").lower() and search_q not in t.category.lower():
                continue

        # Sektör uyumu kontrolü (Madde 2)
        cat_upper = (t.category or "").upper().strip()
        is_sector_rec = any(cat_upper == cs or cs in cat_upper for cs in company_sectors) if company_sectors else False

        # NACE uyumu kontrolü
        is_rec = is_sector_rec
        cat_lower = t.category.lower()
        title_lower = t.title.lower()
        if "62" in nace_joined or "yazılım" in nace_joined or "bilişim" in nace_joined:
            if cat_lower in ["yazılım", "teknoloji", "veri", "analiz", "güvenlik"]:
                is_rec = True
        elif "finans" in nace_joined or "mali" in nace_joined or "64" in nace_joined or "66" in nace_joined:
            if cat_lower in ["finans", "muhasebe", "mali"]:
                is_rec = True
        elif "hukuk" in nace_joined or "69" in nace_joined:
            if cat_lower in ["hukuk", "uyum", "mevzuat"]:
                is_rec = True
        elif "tekstil" in nace_joined or "dokuma" in nace_joined or "13" in nace_joined or "14" in nace_joined:
            if cat_lower in ["tekstil", "üretim", "imalat"]:
                is_rec = True

        item = SystemJobTitleTemplateOut.model_validate(t)
        item.is_nace_recommended = is_rec
        item.is_sector_recommended = is_sector_rec
        out.append(item)

    # Sektör ve NACE önerilenleri önce göster
    out.sort(key=lambda x: (not x.is_sector_recommended, not x.is_nace_recommended, x.category, x.title))
    return out


@router.get("/{tenant_id}/job-titles", response_model=List[CompanyJobTitleOut])
async def list_company_job_titles(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Şirketin tanımladığı ünvanları, bağlı departmanlarını ve aktör sayılarını listeler."""
    await _get_tenant_or_404(db, tenant_id)
    result = await db.execute(
        select(JobTitle).where(JobTitle.tenant_id == tenant_id).order_by(func.lower(JobTitle.title))
    )
    titles = result.scalars().all()

    # Departman isim eşlemesi (Madde 2)
    depts_query = await db.execute(
        select(Department.id, Department.name).where(Department.tenant_id == tenant_id)
    )
    depts_map = dict(depts_query.all())

    # Ünvan bazında aktör sayısını çek
    counts_query = await db.execute(
        select(Actor.job_title_id, func.count(Actor.id))
        .where(Actor.tenant_id == tenant_id, Actor.job_title_id != None)
        .group_by(Actor.job_title_id)
    )
    counts_map = dict(counts_query.all())

    out = []
    for t in titles:
        item = CompanyJobTitleOut.model_validate(t)
        item.actor_count = counts_map.get(t.id, 0)
        item.department_name = depts_map.get(t.department_id) if t.department_id else None
        out.append(item)
    return out


@router.post("/{tenant_id}/job-titles", response_model=CompanyJobTitleOut, status_code=201)
async def create_company_job_title(
    tenant_id: uuid.UUID, payload: CompanyJobTitleIn,
    current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Şirket için yeni ünvan tanımlar.
    - Şirketin tanımladığı departmanlardan biri seçilebilir (Madde 2).
    - Süper Yönetim Konsolundaki ünvanlardan seçilmişse Sistem Rol Promptu otomatik gelir veya kullanıcı yazar.
    - RECAi yeni ünvanı inceler; sistem geneli için faydalı bulursa Ana Şablona ekler.
    """
    tenant = await _get_tenant_or_404(db, tenant_id)
    ent = await entitlements(db, tenant, current)
    if not ent.can_create_custom_titles:
        deny(f"'{ent.plan_name or 'Mevcut'}' paketiniz şirkete özel ünvan tanımlamaya izin vermiyor. Sistem ünvanlarından seçebilir veya paketinizi yükseltebilirsiniz.")

    # Departman doğrulaması (eğer seçildiyse)
    dept_name = None
    if payload.department_id:
        dept = await db.get(Department, payload.department_id)
        if dept and dept.tenant_id == tenant_id:
            dept_name = dept.name
        else:
            payload.department_id = None

    title_clean = payload.title.strip()
    if not title_clean:
        raise HTTPException(status_code=422, detail="Ünvan adı boş bırakılamaz.")

    role_prompt = payload.base_role_prompt.strip()
    if not role_prompt:
        role_prompt = f"Sen RECOrion bünyesinde {payload.category} kategorisinde görev yapan uzman bir {title_clean} personelsin. Görev tanımın: {payload.description or title_clean}."

    # Kod üretimi
    code_raw = payload.code.strip() if payload.code else _slugify_code(title_clean)
    code_safe = code_raw[:60]

    # Şirket içinde aynı kod var mı kontrolü
    existing_in_company = (await db.execute(
        select(JobTitle.id).where(JobTitle.tenant_id == tenant_id, func.lower(JobTitle.code) == code_safe.lower())
    )).first()
    if existing_in_company:
        code_safe = f"{code_safe}_{uuid.uuid4().hex[:4].upper()}"[:60]

    job_title = JobTitle(
        tenant_id=tenant_id,
        department_id=payload.department_id,
        code=code_safe,
        title=title_clean,
        category=payload.category.strip().upper(),
        description=payload.description.strip() if payload.description else None,
        base_role_prompt=role_prompt,
        required_skills=payload.required_skills,
        recommended_tier=await _to_tier(db, payload.recommended_model_code),
        autonomy_level=payload.autonomy_level,
        is_active=True
    )
    db.add(job_title)
    await db.flush()

    # -------------------------------------------------------------
    # RECAi MODELİ KONTROLÜ (Madde 2)
    # -------------------------------------------------------------
    is_beneficial, score, reason = await _evaluate_job_title_with_ai(
        title=title_clean,
        category=payload.category,
        description=payload.description,
        role_prompt=role_prompt,
        db=db
    )

    if is_beneficial:
        job_title.ai_review_status = "PROMOTED_GLOBAL"
        job_title.ai_review_feedback = (
            f"RECAi tarafından incelendi: Sistem geneli için yüksek fayda sağladığı tespit edildi "
            f"(Fayda Skoru: %{score}). Ana şablona otomatik eklendi. {reason}"
        )

        # Ana sistem şablonuna da ekle (tenant_id = None)
        global_code = f"GLOBAL_{code_safe}"[:64]
        existing_global = (await db.execute(
            select(JobTitle.id).where(
                JobTitle.tenant_id == None,
                or_(func.lower(JobTitle.code) == global_code.lower(), func.lower(JobTitle.title) == title_clean.lower())
            )
        )).first()

        if not existing_global:
            global_template = JobTitle(
                tenant_id=None,
                code=global_code,
                title=title_clean,
                category=payload.category.strip().upper(),
                description=payload.description,
                base_role_prompt=role_prompt,
                required_skills=payload.required_skills,
                recommended_tier=await _to_tier(db, payload.recommended_model_code),
                autonomy_level=payload.autonomy_level,
                ai_review_status="PROMOTED_GLOBAL",
                ai_review_feedback=f"Müşteri tanımından RECAi tarafından terfi ettirildi (%{score}): {reason}",
                is_active=True
            )
            db.add(global_template)
    else:
        job_title.ai_review_status = "COMPANY_LOCAL"
        job_title.ai_review_feedback = (
            f"RECAi tarafından incelendi: Şirket operasyonunuza özel yerel ünvan olarak onaylandı "
            f"(Fayda Skoru: %{score}). {reason}"
        )

    await db.commit()
    await db.refresh(job_title)
    out_res = CompanyJobTitleOut.model_validate(job_title)
    out_res.department_name = dept_name
    return out_res


@router.put("/{tenant_id}/job-titles/{title_id}", response_model=CompanyJobTitleOut)
async def update_company_job_title(
    tenant_id: uuid.UUID, title_id: uuid.UUID, payload: CompanyJobTitleIn, db: AsyncSession = Depends(get_db)
):
    """Şirket ünvanını günceller."""
    job_title = await db.get(JobTitle, title_id)
    if not job_title or job_title.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Ünvan bulunamadı.")

    dept_name = None
    if payload.department_id:
        dept = await db.get(Department, payload.department_id)
        if dept and dept.tenant_id == tenant_id:
            dept_name = dept.name
            job_title.department_id = payload.department_id
        else:
            job_title.department_id = None
    else:
        job_title.department_id = None

    job_title.title = payload.title.strip()
    job_title.category = payload.category.strip().upper()
    job_title.description = payload.description.strip() if payload.description else None
    job_title.base_role_prompt = payload.base_role_prompt.strip()
    job_title.required_skills = payload.required_skills
    job_title.recommended_tier = await _to_tier(db, payload.recommended_model_code)  # #349
    job_title.autonomy_level = payload.autonomy_level

    await db.commit()
    await db.refresh(job_title)
    out_res = CompanyJobTitleOut.model_validate(job_title)
    out_res.department_name = dept_name
    return out_res


@router.delete("/{tenant_id}/job-titles/{title_id}")
async def delete_company_job_title(
    tenant_id: uuid.UUID, title_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Şirket ünvanını siler."""
    job_title = await db.get(JobTitle, title_id)
    if not job_title or job_title.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Ünvan bulunamadı.")

    title_name = job_title.title
    await db.delete(job_title)
    await db.commit()
    return {"success": True, "message": f"'{title_name}' ünvanı silindi."}


# ==================================================================
# MADDE 3: AI AJANLARININ İŞE ALIM VE YÖNETİMİ
# ==================================================================
class AIAgentIn(BaseModel):
    display_name: str = Field(..., description="AI Ajan Adı")
    model_code: Optional[str] = Field(None, description="RECAi adı (MERGEN, HIZLI, DERIN); eski model kodu da kabul edilir")
    recai_capabilities: Optional[Dict[str, bool]] = Field(None, description="#349: RECAi Görsel/Ses/Okur bu personelde açık mı")
    job_title_id: Optional[uuid.UUID] = Field(None, description="Şirket unvanı")
    catalog_title_id: Optional[uuid.UUID] = Field(None, description="Platform kataloğundan unvan (işe alımda şirkete eklenir)")
    department_id: Optional[uuid.UUID] = Field(None, description="Şirket departmanı")
    catalog_department_id: Optional[uuid.UUID] = Field(None, description="Katalog departmanı (işe alımda şirkete eklenir)")
    description: Optional[str] = Field(None, description="AI Ajan Açıklaması")
    hired_at: Optional[datetime] = Field(None, description="İşe Alım Tarihi (Tanımlama Tarihi)")
    autonomy_level: str = Field("L1", description="Otonomi Seviyesi (L1, L2, L3)")
    system_prompt: Optional[str] = Field(None, description="Özel Sistem Promptu")
    pending_learnings: Optional[List[Dict[str, Any]]] = Field(None, description="Tanımlama anında Deep Search ile elde edilen öğrenim maddeleri")
    deep_search_metadata: Optional[Dict[str, Any]] = Field(None, description="Deep search rapor metadatası (sektör, ünvan, özetler)")



class AIAgentUpdateIn(BaseModel):
    display_name: Optional[str] = None
    model_code: Optional[str] = None  # #349: RECAi adı (eski model kodu da kabul edilir)
    recai_capabilities: Optional[Dict[str, bool]] = None
    job_title_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    hired_at: Optional[datetime] = None
    autonomy_level: Optional[str] = None
    system_prompt: Optional[str] = None
    daily_cost_try: Optional[float] = Field(None, ge=0, le=10_000_000)  # isteğe bağlı günlük sabit maliyet (ADIM 7.5.2)
    clear_daily_cost: bool = False


class AIAgentTerminateIn(BaseModel):
    dismissed_at: Optional[datetime] = Field(None, description="İşten Çıkarılma / Pasife Çekilme Tarihi")
    reason: Optional[str] = Field(None, description="Pasife Çekilme Nedeni")


class AIAgentOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    actor_type: str
    display_name: str
    role: str
    status: str
    description: Optional[str] = None
    hired_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    autonomy_level: str = "L1"
    system_prompt: Optional[str] = None
    preferred_model_id: Optional[uuid.UUID] = None
    model_code: Optional[str] = None  # #349: RECAi adının kodu (MERGEN, HIZLI, DERIN) — gerçek model gönderilmez
    model_display_name: Optional[str] = None  # #349: RECAi adı
    recai_tier: Optional[str] = None
    recai_capabilities: Dict[str, Any] = {}
    job_title_id: Optional[uuid.UUID] = None
    job_title_name: Optional[str] = None
    job_title_code: Optional[str] = None
    job_title_category: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    document_count: int = 0
    daily_cost_try: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LLMModelOptionOut(BaseModel):
    id: uuid.UUID
    model_code: str
    display_name: str
    model_type: str
    status: str

    class Config:
        from_attributes = True


@router.get("/{tenant_id}/entitlements")
async def get_company_entitlements(
    tenant_id: uuid.UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Şirketin paketine göre kullanabileceği özellikler (arayüz düğmeleri buna göre açılır/kapanır)."""
    tenant = await _get_tenant_or_404(db, tenant_id)
    return (await entitlements(db, tenant, current)).as_dict()


def _tier_code(actor) -> str:
    """#349: AI personelin RECAi adı (seçilmemişse Mergen)."""
    return actor.recai_tier or recai.DEFAULT_TIER


async def _to_tier(db: AsyncSession, value: Optional[str]) -> Optional[str]:
    """RECAi adı (MERGEN/HIZLI/DERIN) ya da eski model kodu → RECAi adı."""
    v = (value or "").strip()
    if not v:
        return None
    if v.upper() in recai.CHAT_TIERS:
        return v.upper()
    return recai.tier_for_model(v, await recai.tiers(db)) or recai.DEFAULT_TIER


def _clean_caps(caps: Optional[Dict[str, Any]], ent) -> Dict[str, bool]:
    """Personel bazında RECAi Görsel/Ses/Okur: paketinde olmayan yetenek açılamaz."""
    out = {}
    for code in recai.CAPABILITY_FEATURE:
        v = (caps or {}).get(code)
        if v is None:
            continue
        out[code] = bool(v) and bool(ent.capabilities.get(code))
    return out


def _forced_model_code(ent, job_title) -> Optional[str]:
    """LLM değiştirme izni yoksa kullanılacak model: ünvanın önerdiği (pakette varsa) ya da paketin ilk modeli."""
    rec = (job_title.recommended_model_code or "").lower() if job_title else ""
    if rec and ent.model_allowed(rec):
        return rec
    return ent.allowed_models[0] if ent.allowed_models else (rec or None)


@router.get("/{tenant_id}/llm-models")
async def list_available_llm_models(tenant_id: uuid.UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """#349: müşterinin seçebileceği RECAi adları (Mergen, Hızlı, Derin). Gerçek EVREN model adları müşteriye gönderilmez.
    Yanıt eski alan adlarını korur (model_code = RECAi kodu, display_name = RECAi adı)."""
    tenant = await _get_tenant_or_404(db, tenant_id)
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    opts = await recai.options(db, plan, bypass=current.is_super_admin or tenant.slug == "recdx_hq")
    return [{**o, "id": o["code"], "status": "ACTIVE"} for o in opts if o["available"]]


@router.get("/{tenant_id}/recai")
async def recai_options(tenant_id: uuid.UUID, current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """#349: paketteki RECAi adları ve yetenekler (Görsel/Ses/Okur); paketinde olmayanlar kilitli gösterilir."""
    tenant = await _get_tenant_or_404(db, tenant_id)
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    bypass = current.is_super_admin or tenant.slug == "recdx_hq"
    return {"tiers": await recai.options(db, plan, bypass=bypass), "capabilities": await recai.capability_options(db, plan, bypass=bypass),
            "default": recai.DEFAULT_TIER, "infra_note": "RECAi, EVREN (Türkiye) yapay zeka altyapısında çalışır."}


class GenerateRolePromptIn(BaseModel):
    title: str = Field(..., description="Ünvan Adı")
    category: Optional[str] = Field("GENEL", description="Sektör / Kategori")
    description: Optional[str] = Field(None, description="Görev Tanımı / Açıklama")
    required_skills: Optional[List[str]] = Field(default_factory=list, description="Gerekli Beceriler")
    model_code: Optional[str] = Field(None, description="Promptu üretecek LLM Modeli (boşsa platform varsayılanı)")
    autonomy_level: Optional[str] = Field("L1", description="Otonomi Seviyesi")


@router.post("/{tenant_id}/generate-role-prompt")
async def generate_company_role_prompt(
    tenant_id: uuid.UUID,
    payload: GenerateRolePromptIn,
    db: AsyncSession = Depends(get_db)
):
    """
    Şirket ünvanı veya AI Ajanı için seçilen EVREN AI Modeli ile Sistem Rol Promptu (Persona & Talimatlar) üretir.
    """
    tenant = await _get_tenant_or_404(db, tenant_id)
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext

    title_clean = (payload.title or "").strip()
    if not title_clean:
        raise HTTPException(status_code=422, detail="Ünvan adı boş bırakılamaz.")

    skills_str = ", ".join(payload.required_skills) if payload.required_skills else "Genel Uzmanlık, Kalite Güvencesi"
    category = payload.category or "GENEL"
    desc = payload.description or f"{title_clean} rolüne ait temel kurumsal iş süreçleri"
    autonomy = payload.autonomy_level or "L1"

    prompt_instruction = f"""Sen RECOrion Kurumsal Yapay Zeka platformunun Sistem Mimarı ve Yetenek Tasarımcısısın.
'{tenant.name}' şirketi için aşağıdaki parametrelere sahip bir yapay zeka aktörü/iş ünvanı için profesyonel, deterministik ve kapsamlı bir 'Sistem Rol Promptu (Persona, Misyon & Talimatlar)' hazırla:

Şirket Adı: {tenant.name}
Ünvan / Pozisyon: {title_clean}
Sektör / Kategori: {category}
Görev Açıklaması: {desc}
Gerekli Beceriler: {skills_str}
Hedef Otonomi Seviyesi: {autonomy}

Rol Promptu Yapısı:
1. Rol ve Kimlik Tanımı (Kimsin, şirket içerisindeki misyonun ve duruşun ne?)
2. Temel Sorumluluklar ve Çalışma İlkeleri (Günlük operasyonlarda ne yaparsın?)
3. Kalite Kapıları ve Çıktı Standartları (Çıktı üretirken hangi kriterleri denetlersin?)
4. Kurumsal İletişim, Güvenlik ve Gizlilik Protokolleri
5. Otonomi & Onay Mekanizması ({autonomy} seviyesine uygun hareket tarzı)

Lütfen doğrudan sistem promptu (persona yönergesi) olarak kullanılacak markdown formatındaki metni Türkçe olarak üret. Başka giriş veya selamlama cümlesi ekleme."""

    messages = [
        {"role": "system", "content": f"Sen {tenant.name} şirketi için uzman AI Rol Promptu ve Persona Tasarımcısısın."},
        {"role": "user", "content": prompt_instruction}
    ]
    # Hata olursa genel şablon döndürülmez; kullanıcı AI servisinin yanıt veremediğini görür
    result = await llm_gateway.chat(
        LLMContext(tenant_id=tenant.id, purpose="ROLE_PROMPT"), messages,
        model_code=payload.model_code, temperature=0.7, max_tokens=6144, timeout=120,
    )
    return {
        "success": True,
        "model_code": result.public_model,
        "role_prompt": result.content.strip(),
        "credits": result.credits,
    }


@router.get("/{tenant_id}/ai-agents", response_model=List[AIAgentOut])
async def list_company_ai_agents(
    tenant_id: uuid.UUID,
    status: Optional[str] = Query(None, description="Durum filtresi (IDLE, WORKING, DISABLED vb.)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Şirket bünyesindeki AI Ajan kadrosunu (işe alınan / pasife çekilen) listeler.
    Model, ünvan ve departman ilişkilerini tek seferde zenginleştirir.
    """
    await _get_tenant_or_404(db, tenant_id)

    stmt = select(Actor).where(
        Actor.tenant_id == tenant_id,
        Actor.actor_type == "AI_AGENT"
    )
    if status:
        stmt = stmt.where(Actor.status == status)
    stmt = stmt.order_by(Actor.created_at.desc())

    actors = (await db.execute(stmt)).scalars().all()

    # İlgili model, job_title ve departmanları topla
    model_ids = {a.preferred_model_id for a in actors if a.preferred_model_id}
    job_title_ids = {a.job_title_id for a in actors if a.job_title_id}
    department_ids = {a.department_id for a in actors if a.department_id}

    models_map = {}
    if model_ids:
        res = await db.execute(select(LLMModel).where(LLMModel.id.in_(model_ids)))
        for m in res.scalars().all():
            models_map[m.id] = m

    titles_map = {}
    if job_title_ids:
        res = await db.execute(select(JobTitle).where(JobTitle.id.in_(job_title_ids)))
        for t in res.scalars().all():
            titles_map[t.id] = t

    depts_map = {}
    if department_ids:
        res = await db.execute(select(Department).where(Department.id.in_(department_ids)))
        for d in res.scalars().all():
            depts_map[d.id] = d

    # Ajanlara ait doküman sayılarını topla
    doc_counts_stmt = select(
        AgentDocument.agent_id,
        func.count(AgentDocument.id).label("count")
    ).where(
        AgentDocument.tenant_id == tenant_id
    ).group_by(AgentDocument.agent_id)
    doc_counts_res = (await db.execute(doc_counts_stmt)).all()
    doc_counts_map = {r[0]: r[1] for r in doc_counts_res}

    out = []
    for a in actors:
        model = models_map.get(a.preferred_model_id)
        title = titles_map.get(a.job_title_id)
        dept = depts_map.get(a.department_id)

        item = AIAgentOut(
            id=a.id,
            tenant_id=a.tenant_id,
            actor_type=a.actor_type,
            display_name=a.display_name,
            role=a.role,
            status=a.status,
            description=a.description,
            hired_at=a.hired_at,
            dismissed_at=a.dismissed_at,
            autonomy_level=a.autonomy_level or "L1",
            system_prompt=a.system_prompt,
            preferred_model_id=a.preferred_model_id,
            daily_cost_try=float(a.daily_cost_try) if a.daily_cost_try is not None else None,
            model_code=_tier_code(a),
            model_display_name=recai.TIER_NAMES.get(_tier_code(a)),
            recai_tier=_tier_code(a),
            recai_capabilities=a.recai_capabilities or {},
            job_title_id=a.job_title_id,
            job_title_name=title.title if title else None,
            job_title_code=title.code if title else None,
            job_title_category=title.category if title else None,
            department_id=a.department_id,
            department_name=dept.name if dept else None,
            document_count=doc_counts_map.get(a.id, 0),
            created_at=a.created_at
        )
        out.append(item)
    return out


@router.post("/{tenant_id}/ai-agents", response_model=AIAgentOut, status_code=201)
async def hire_ai_agent(
    tenant_id: uuid.UUID, payload: AIAgentIn,
    current: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """
    Şirket bünyesinde yeni bir AI Ajanı işe alır / tanımlar (Madde 3).
    - AI Ajan Adı
    - AI Ajan LLM Modeli
    - AI Ajan Ünvanı (Şirkete tanımlanan ünvanlardan seçilir)
    - AI Ajan Açıklaması
    - AI Ajan İşe Alım Tarihi (Tanımlama Tarihi)
    """
    tenant = await _get_tenant_or_404(db, tenant_id)

    # -------------------------------------------------------------
    # MADDE 5: PAKET AI AJAN KOTASI KONTROLÜ
    # -------------------------------------------------------------
    if tenant.plan_id:
        plan = await db.get(Plan, tenant.plan_id)
        if plan and plan.max_agents is not None:
            active_count_stmt = select(func.count(Actor.id)).where(
                Actor.tenant_id == tenant_id,
                Actor.actor_type == "AI_AGENT",
                Actor.status != "DISABLED"
            )
            active_count = (await db.execute(active_count_stmt)).scalar() or 0
            if active_count >= plan.max_agents:
                raise HTTPException(
                    status_code=403,
                    detail=f"Satın aldığınız '{plan.name}' paketinin azami AI Ajan kotası ({plan.max_agents} Ajan) dolmuştur. Yeni bir AI Ajanı tanımlayamazsınız. Lütfen paketinizi yükseltin veya mevcut bir ajanı pasife çekin."
                )

    name = payload.display_name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="AI Ajan adı boş bırakılamaz.")

    # 1-2. Sektör > Departman > Unvan: katalog seçimleri şirkete aktarılır (ADIM 5.3)
    from app.services.hiring import render_role_prompt, resolve_hire_target
    job_title, dept = await resolve_hire_target(
        db, tenant, job_title_id=payload.job_title_id, catalog_title_id=payload.catalog_title_id,
        department_id=payload.department_id, catalog_department_id=payload.catalog_department_id,
    )
    dept_name = dept.name if dept else None

    # 3. RECAi adı (#349; paket izinleri #241): müşteri model değil RECAi adı seçer, modeli RECDx çözer
    ent = await entitlements(db, tenant, current)
    from app.services.hiring import default_agent_tier
    forced = default_agent_tier(ent, job_title)
    tier = await _to_tier(db, payload.model_code) or forced
    if not ent.can_change_llm and tier != forced:
        deny(f"'{ent.plan_name}' paketiniz RECAi seçimini değiştirmeye izin vermiyor; bu ünvan için {recai.TIER_NAMES[forced]} kullanılır.")
    if not ent.tier_allowed(tier):
        deny(f"{recai.TIER_NAMES.get(tier, tier)} '{ent.plan_name}' paketinizde yer almıyor.")
    preferred_model_id = None

    # 4. Sistem Rol Promptu (Özel verilmemişse ünvandan devralınır; paket izin vermiyorsa değiştirilemez).
    # {{company_name}} / {{department_name}} yer tutucuları şirket ve departman adıyla doldurulur.
    raw_prompt = (job_title.base_role_prompt or "").strip()
    base_prompt = render_role_prompt(raw_prompt, tenant.name, dept_name)
    custom_prompt = (payload.system_prompt or "").strip()
    if custom_prompt and custom_prompt not in (base_prompt, raw_prompt) and not ent.can_edit_role_prompt:
        deny(f"'{ent.plan_name}' paketiniz ünvan rol promptunu değiştirmeye izin vermiyor; ünvanın hazır rol promptu kullanılır.")
    role_prompt = render_role_prompt(custom_prompt, tenant.name, dept_name) if custom_prompt else         (base_prompt or f"Sen bir {job_title.title} AI personelsin.")

    # 5. İşe Alım Tarihi (Payload'da varsa o, yoksa şu an)
    hire_date = payload.hired_at or datetime.utcnow()

    # 6. Benzersiz kod/rol adı
    role_code = job_title.code or "AGENT"

    agent = Actor(
        tenant_id=tenant_id,
        actor_type="AI_AGENT",
        display_name=name,
        role=role_code,
        job_title_id=job_title.id,
        department_id=dept.id if dept else None,
        preferred_model_id=preferred_model_id,
        recai_tier=tier,
        recai_capabilities=_clean_caps(payload.recai_capabilities, ent),
        system_prompt=role_prompt,
        description=payload.description.strip() if payload.description else None,
        autonomy_level=payload.autonomy_level or job_title.autonomy_level or "L1",
        status="IDLE",
        hired_at=hire_date,
        dismissed_at=None
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    # Tanımlama anında Sektör & Ünvan Deep Search yapılmışsa hafızaya ve dokümanlara işle
    if payload.pending_learnings:
        try:
            from app.services.agent_learning_service import agent_learning_service
            meta = payload.deep_search_metadata or {}
            await agent_learning_service.save_pending_learnings_for_agent(
                tenant_id=tenant_id,
                agent_id=agent.id,
                learnings=payload.pending_learnings,
                sector_name=meta.get("sector_name") or "Şirket Sektörü",
                job_title_name=job_title.title,
                sector_summary=meta.get("sector_summary") or "",
                job_title_summary=meta.get("job_title_summary") or "",
                sources=meta.get("sources") or [],
                db=db
            )
        except Exception as e:
            logger.warning(f"Ajan işe alımında bekleyen Deep Search öğrenimlerini kaydetme hatası: {e}")

    return AIAgentOut(
        id=agent.id,
        tenant_id=agent.tenant_id,
        actor_type=agent.actor_type,
        display_name=agent.display_name,
        role=agent.role,
        status=agent.status,
        description=agent.description,
        hired_at=agent.hired_at,
        dismissed_at=agent.dismissed_at,
        autonomy_level=agent.autonomy_level,
        system_prompt=agent.system_prompt,
        preferred_model_id=agent.preferred_model_id,
        daily_cost_try=float(agent.daily_cost_try) if agent.daily_cost_try is not None else None,
        model_code=_tier_code(agent),
        model_display_name=recai.TIER_NAMES.get(_tier_code(agent)),
        recai_tier=_tier_code(agent),
        recai_capabilities=agent.recai_capabilities or {},
        job_title_id=job_title.id,
        job_title_name=job_title.title,
        job_title_code=job_title.code,
        job_title_category=job_title.category,
        department_id=agent.department_id,
        department_name=dept_name,
        created_at=agent.created_at
    )


@router.put("/{tenant_id}/ai-agents/{agent_id}", response_model=AIAgentOut)
async def update_ai_agent(
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: AIAgentUpdateIn,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """AI Ajan bilgilerini (Adı, Modeli, Ünvanı, Departmanı, Açıklaması) günceller."""
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI Ajan bulunamadı.")
    ent = await entitlements(db, await _get_tenant_or_404(db, tenant_id), current)

    if payload.display_name is not None:
        clean_name = payload.display_name.strip()
        if not clean_name:
            raise HTTPException(status_code=422, detail="Ajan adı boş bırakılamaz.")
        agent.display_name = clean_name

    if payload.description is not None:
        agent.description = payload.description.strip() or None

    if payload.hired_at is not None:
        agent.hired_at = payload.hired_at

    if payload.autonomy_level is not None:
        agent.autonomy_level = payload.autonomy_level

    if payload.clear_daily_cost:
        agent.daily_cost_try = None
    elif payload.daily_cost_try is not None:
        agent.daily_cost_try = payload.daily_cost_try
    if payload.system_prompt is not None:
        new_prompt = payload.system_prompt.strip()
        if new_prompt != (agent.system_prompt or "").strip() and not ent.can_edit_role_prompt:
            deny(f"'{ent.plan_name}' paketiniz rol promptunu değiştirmeye izin vermiyor.")
        agent.system_prompt = new_prompt

    if payload.job_title_id is not None:
        title = await db.get(JobTitle, payload.job_title_id)
        if not title or (title.tenant_id is not None and title.tenant_id != tenant_id):
            raise HTTPException(status_code=404, detail="Seçilen ünvan bulunamadı.")
        agent.job_title_id = title.id
        agent.role = title.code or agent.role

    if payload.department_id is not None:
        dept = await db.get(Department, payload.department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Seçilen departman bulunamadı.")
        agent.department_id = dept.id

    if payload.model_code is not None:  # #349: RECAi adı
        tier = await _to_tier(db, payload.model_code)
        if tier and tier != _tier_code(agent):
            if not ent.can_change_llm:
                deny(f"'{ent.plan_name}' paketiniz RECAi seçimini değiştirmeye izin vermiyor.")
            if not ent.tier_allowed(tier):
                deny(f"{recai.TIER_NAMES.get(tier, tier)} '{ent.plan_name}' paketinizde yer almıyor.")
            agent.recai_tier, agent.preferred_model_id = tier, None
    if payload.recai_capabilities is not None:
        agent.recai_capabilities = _clean_caps(payload.recai_capabilities, ent)

    await db.commit()
    await db.refresh(agent)

    # Zenginleştirilmiş yanıt dön
    model = await db.get(LLMModel, agent.preferred_model_id) if agent.preferred_model_id else None
    title = await db.get(JobTitle, agent.job_title_id) if agent.job_title_id else None
    dept = await db.get(Department, agent.department_id) if agent.department_id else None

    return AIAgentOut(
        id=agent.id,
        tenant_id=agent.tenant_id,
        actor_type=agent.actor_type,
        display_name=agent.display_name,
        role=agent.role,
        status=agent.status,
        description=agent.description,
        hired_at=agent.hired_at,
        dismissed_at=agent.dismissed_at,
        autonomy_level=agent.autonomy_level,
        system_prompt=agent.system_prompt,
        preferred_model_id=agent.preferred_model_id,
        daily_cost_try=float(agent.daily_cost_try) if agent.daily_cost_try is not None else None,
        model_code=_tier_code(agent),
        model_display_name=recai.TIER_NAMES.get(_tier_code(agent)),
        recai_tier=_tier_code(agent),
        recai_capabilities=agent.recai_capabilities or {},
        job_title_id=title.id if title else None,
        job_title_name=title.title if title else None,
        job_title_code=title.code if title else None,
        job_title_category=title.category if title else None,
        department_id=dept.id if dept else None,
        department_name=dept.name if dept else None,
        created_at=agent.created_at
    )


@router.post("/{tenant_id}/ai-agents/{agent_id}/terminate", response_model=AIAgentOut)
async def terminate_ai_agent(
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: AIAgentTerminateIn,
    db: AsyncSession = Depends(get_db)
):
    """
    AI Ajanını işten çıkarır / pasife çeker (Madde 3).
    - Durumu 'DISABLED' olarak ayarlar.
    - İşten Çıkma Tarihini (`dismissed_at`) kaydeder.
    """
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI Ajan bulunamadı.")

    agent.status = "DISABLED"
    agent.dismissed_at = payload.dismissed_at or datetime.utcnow()
    await db.commit()
    await db.refresh(agent)

    model = await db.get(LLMModel, agent.preferred_model_id) if agent.preferred_model_id else None
    title = await db.get(JobTitle, agent.job_title_id) if agent.job_title_id else None
    dept = await db.get(Department, agent.department_id) if agent.department_id else None

    return AIAgentOut(
        id=agent.id,
        tenant_id=agent.tenant_id,
        actor_type=agent.actor_type,
        display_name=agent.display_name,
        role=agent.role,
        status=agent.status,
        description=agent.description,
        hired_at=agent.hired_at,
        dismissed_at=agent.dismissed_at,
        autonomy_level=agent.autonomy_level,
        system_prompt=agent.system_prompt,
        preferred_model_id=agent.preferred_model_id,
        daily_cost_try=float(agent.daily_cost_try) if agent.daily_cost_try is not None else None,
        model_code=_tier_code(agent),
        model_display_name=recai.TIER_NAMES.get(_tier_code(agent)),
        recai_tier=_tier_code(agent),
        recai_capabilities=agent.recai_capabilities or {},
        job_title_id=title.id if title else None,
        job_title_name=title.title if title else None,
        job_title_code=title.code if title else None,
        job_title_category=title.category if title else None,
        department_id=dept.id if dept else None,
        department_name=dept.name if dept else None,
        created_at=agent.created_at
    )


@router.post("/{tenant_id}/ai-agents/{agent_id}/rehire", response_model=AIAgentOut)
async def rehire_ai_agent(
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Pasife alınmış AI Ajanını yeniden işe alır / aktif eder."""
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI Ajan bulunamadı.")

    tenant = await _get_tenant_or_404(db, tenant_id)

    # -------------------------------------------------------------
    # MADDE 5: YENİDEN İŞE ALIMDA DA KOTA KONTROLÜ
    # -------------------------------------------------------------
    if tenant.plan_id:
        plan = await db.get(Plan, tenant.plan_id)
        if plan and plan.max_agents is not None:
            active_count_stmt = select(func.count(Actor.id)).where(
                Actor.tenant_id == tenant_id,
                Actor.actor_type == "AI_AGENT",
                Actor.status != "DISABLED",
                Actor.id != agent_id
            )
            active_count = (await db.execute(active_count_stmt)).scalar() or 0
            if active_count >= plan.max_agents:
                raise HTTPException(
                    status_code=403,
                    detail=f"Paketinizin azami AI Ajan kotası ({plan.max_agents} Ajan) dolmuştur. Bu ajanı tekrar aktif edebilmek için paketinizi yükseltiniz."
                )

    agent.status = "IDLE"
    agent.dismissed_at = None
    agent.hired_at = datetime.utcnow()
    await db.commit()
    await db.refresh(agent)

    model = await db.get(LLMModel, agent.preferred_model_id) if agent.preferred_model_id else None
    title = await db.get(JobTitle, agent.job_title_id) if agent.job_title_id else None
    dept = await db.get(Department, agent.department_id) if agent.department_id else None

    return AIAgentOut(
        id=agent.id,
        tenant_id=agent.tenant_id,
        actor_type=agent.actor_type,
        display_name=agent.display_name,
        role=agent.role,
        status=agent.status,
        description=agent.description,
        hired_at=agent.hired_at,
        dismissed_at=agent.dismissed_at,
        autonomy_level=agent.autonomy_level,
        system_prompt=agent.system_prompt,
        preferred_model_id=agent.preferred_model_id,
        daily_cost_try=float(agent.daily_cost_try) if agent.daily_cost_try is not None else None,
        model_code=_tier_code(agent),
        model_display_name=recai.TIER_NAMES.get(_tier_code(agent)),
        recai_tier=_tier_code(agent),
        recai_capabilities=agent.recai_capabilities or {},
        job_title_id=title.id if title else None,
        job_title_name=title.title if title else None,
        job_title_code=title.code if title else None,
        job_title_category=title.category if title else None,
        department_id=dept.id if dept else None,
        department_name=dept.name if dept else None,
        created_at=agent.created_at
    )


@router.delete("/{tenant_id}/ai-agents/{agent_id}")
async def delete_ai_agent(tenant_id: uuid.UUID, agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """AI Ajanını sistemden tamamen siler."""
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI Ajan bulunamadı.")

    name = agent.display_name
    await db.delete(agent)
    await db.commit()
    return {"success": True, "message": f"'{name}' AI ajanı silindi."}


@router.get("/{tenant_id}/agent-quota")
async def get_company_agent_quota(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Şirketin AI Ajan kotası ve kullanım durumunu döner (Madde 5)."""
    tenant = await _get_tenant_or_404(db, tenant_id)
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None

    active_count_stmt = select(func.count(Actor.id)).where(
        Actor.tenant_id == tenant_id,
        Actor.actor_type == "AI_AGENT",
        Actor.status != "DISABLED"
    )
    active_count = (await db.execute(active_count_stmt)).scalar() or 0
    max_limit = plan.max_agents if (plan and plan.max_agents is not None) else 5

    return {
        "active_agents": active_count,
        "max_agents": max_limit,
        "plan_name": plan.name if plan else "Temel Paket",
        "is_limit_reached": active_count >= max_limit
    }


# ==================================================================
# AI AJANLARI UZMANLIK / KAYNAK DOKÜMANLARI & RAG HAFIZA ENTEGRASYONU (Madde 2)
# ==================================================================
class AgentDocumentOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    agent_id: uuid.UUID
    file_name: str
    original_name: str
    file_type: str
    file_size: int
    storage_path: Optional[str] = None
    extracted_text_preview: Optional[str] = None
    summary: Optional[str] = None
    status: str
    memory_item_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AddWebLinkIn(BaseModel):
    url: str = Field(..., description="Öğrenilecek Web Sayfası URL'si (http/https)")
    title: Optional[str] = Field(None, description="Opsiyonel web sayfası başlığı veya konusu")


class AddVideoLinkIn(BaseModel):
    url: str = Field(..., description="YouTube video URL'si (watch?v=, youtu.be, shorts)")
    title: Optional[str] = Field(None, description="Opsiyonel video başlığı")


async def fetch_web_page_content(url: str) -> Dict[str, Any]:
    """
    Belirtilen web URL'sinden HTML içeriğini çeker, temiz metne dönüştürür ve başlığı ayıklar.
    """
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 RECOrionBot/1.0"
    }
    try:
        resp = await safe_request("GET", clean_url, timeout=25.0, headers=headers)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=400, detail=f"Bu adres öğrenme kaynağı olarak kullanılamaz: {exc}")
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "header", "footer", "nav"]):
        tag.decompose()

    page_title = ""
    if soup.title and soup.title.string:
        page_title = soup.title.string.strip()
    elif soup.find("meta", property="og:title"):
        page_title = soup.find("meta", property="og:title").get("content", "").strip()
    if not page_title:
        page_title = clean_url.split("//")[-1].split("/")[0]

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)

    return {
        "url": clean_url,
        "title": page_title[:200],
        "text": clean_text
    }


def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    YouTube URL'sinden 11 haneli video ID'sini ayıklar.
    """
    pattern = r'(?:v=|\/embed\/|\/shorts\/|youtu\.be\/|\/v\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None


async def fetch_youtube_content(url: str) -> Dict[str, Any]:
    """
    YouTube videosunun başlığını, kanal bilgisini ve altyazı/transkript metnini çeker.
    """
    clean_url = url.strip()
    video_id = extract_youtube_video_id(clean_url)
    if not video_id:
        raise ValueError("Geçerli bir YouTube video bağlantısı tespit edilemedi.")

    title = f"YouTube Video ({video_id})"
    author = "YouTube"
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(oembed_url)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", title)
                author = data.get("author_name", author)
    except Exception as e:
        logger.warning(f"YouTube oEmbed bilgisi alınamadı ({video_id}): {e}")

    transcript_text = ""
    try:
        loop = asyncio.get_event_loop()
        def _fetch_subtitles():
            api = YouTubeTranscriptApi()
            return api.fetch(video_id, languages=['tr', 'en', 'de', 'fr', 'es', 'az'])

        fetched = await loop.run_in_executor(None, _fetch_subtitles)
        lines = [snippet.text for snippet in fetched if snippet.text]
        transcript_text = " ".join(lines)
    except Exception as e:
        logger.info(f"YouTube transkripti çekilemedi veya altyazı kapalı ({video_id}): {e}")

    if transcript_text:
        combined_text = (
            f"--- YOUTUBE VİDEO BİLGİSİ ---\n"
            f"Başlık: {title}\n"
            f"Kanal / Yayıncı: {author}\n"
            f"Video ID: {video_id}\n"
            f"Video URL: https://www.youtube.com/watch?v={video_id}\n\n"
            f"--- VİDEO TRANSKRİPT & ALTYAZI METNİ ---\n"
            f"{transcript_text}"
        )
    else:
        combined_text = (
            f"--- YOUTUBE VİDEO BİLGİSİ ---\n"
            f"Başlık: {title}\n"
            f"Kanal / Yayıncı: {author}\n"
            f"Video ID: {video_id}\n"
            f"Video URL: https://www.youtube.com/watch?v={video_id}\n\n"
            f"Not: Bu videoya ait otomatik altyazı/transkript bulunamadı veya kapalı. "
            f"Video başlığı ve meta verileri ajanın hafıza kütüphanesine referans olarak kaydedildi."
        )

    return {
        "video_id": video_id,
        "title": title[:200],
        "author": author[:100],
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "transcript": transcript_text,
        "combined_text": combined_text
    }



def extract_text_from_file(file_bytes: bytes, file_ext: str) -> str:
    """
    Desteklenen dosya tiplerinden (PDF, DOCX, XLSX, TXT, CSV, MD, JSON) metin çıkarır.
    """
    ext = file_ext.lower().lstrip(".")
    text = ""
    try:
        if ext == "pdf":
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pages_text.append(extracted.strip())
            text = "\n\n".join(pages_text)
        elif ext in ["docx", "doc"]:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)
            text = "\n".join(paragraphs)
        elif ext in ["xlsx", "xls"]:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            sheet_texts = []
            for sheetname in wb.sheetnames:
                sheet = wb[sheetname]
                rows_text = []
                for row in sheet.iter_rows(values_only=True):
                    row_vals = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                    if row_vals:
                        rows_text.append(" | ".join(row_vals))
                if rows_text:
                    sheet_texts.append(f"--- Sayfa: {sheetname} ---\n" + "\n".join(rows_text))
            text = "\n\n".join(sheet_texts)
        elif ext in ["txt", "csv", "md", "json", "xml", "log", "yaml", "yml"]:
            for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1254"]:
                try:
                    text = file_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
        else:
            try:
                text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                text = ""
    except Exception as e:
        logger.warning(f"Doküman metin ayrıştırma hatası ({ext}): {e}")
    return text.strip()


@router.post("/{tenant_id}/ai-agents/{agent_id}/web-links", response_model=AgentDocumentOut, status_code=201)
async def add_agent_web_link(
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    data: AddWebLinkIn,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI Ajanına araştırma yapması ve öğrenmesi için bir Web Sayfası URL'si tanımlar.
    Web sayfasının içeriğini çeker, temizler ve ajanın hafızasına (Qdrant & MemoryItem) kaydeder.
    """
    await _get_tenant_or_404(db, tenant_id)
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI Ajan bulunamadı.")
    await ensure_document_quota(db, await entitlements(db, await _get_tenant_or_404(db, tenant_id), current), tenant_id, agent_id, 0)

    if not data.url or not data.url.strip():
        raise HTTPException(status_code=400, detail="Web sayfası URL'si boş olamaz.")

    try:
        scraped = await fetch_web_page_content(data.url)
    except Exception as e:
        logger.error(f"Web sayfası çekme hatası: {e}")
        raise HTTPException(status_code=400, detail=f"Web sayfası içeriği alınamadı veya erişilemedi: {str(e)}")

    page_url = scraped["url"]
    page_title = (data.title.strip() if data.title and data.title.strip() else scraped["title"]) or page_url
    extracted_text = scraped["text"]
    if not extracted_text:
        extracted_text = f"Web Sayfası Başlığı: {page_title}\nBağlantı: {page_url}\nİçerik tespit edilemedi."

    content_size = len(extracted_text.encode("utf-8"))
    summary_text = f"🌐 Web Sayfası: {page_title}\nURL: {page_url}\n{extracted_text[:250]}..."

    # 1. Kolektif Hafıza (MemoryItem)
    memory_item = MemoryItem(
        tenant_id=tenant_id,
        scope="AGENT",
        agent_id=agent_id,
        source_reference=page_url,
        content=extracted_text[:20000],
        metadata_json={
            "source_type": "web",
            "url": page_url,
            "title": page_title,
            "agent_name": agent.display_name
        },
        status="APPROVED",
        confidence_score=1.0
    )
    db.add(memory_item)
    await db.flush()

    # 2. Qdrant Vektör Hafızası
    try:
        from app.services.collective_memory import collective_memory
        point = await collective_memory.add_memory(
            tenant_id=str(tenant_id),
            scope="AGENT",
            agent_id=str(agent_id),
            source_reference=page_url,
            content=extracted_text[:10000],
            metadata={
                "source_type": "web",
                "url": page_url,
                "title": page_title,
                "agent_name": agent.display_name,
                "memory_item_id": str(memory_item.id)
            }
        )
        memory_item.qdrant_point_id = uuid.UUID(str(point["point_id"]))  # geri alma/terfi aynı vektörü kullanır (ADIM 8.4)
    except Exception as e:
        logger.warning(f"Qdrant web hafıza indeksleme uyarısı: {e}")

    # 3. AgentDocument Kaydı
    doc = AgentDocument(
        tenant_id=tenant_id,
        agent_id=agent_id,
        file_name=f"web_{uuid.uuid4().hex[:8]}",
        original_name=page_title,
        file_type="web",
        file_size=content_size,
        storage_path=page_url,
        extracted_text=extracted_text[:100000],
        summary=summary_text,
        status="INDEXED",
        memory_item_id=memory_item.id
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    preview = doc.extracted_text[:400] + ("..." if len(doc.extracted_text) > 400 else "")
    return AgentDocumentOut(
        id=doc.id,
        tenant_id=doc.tenant_id,
        agent_id=doc.agent_id,
        file_name=doc.file_name,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        storage_path=doc.storage_path,
        extracted_text_preview=preview,
        summary=doc.summary,
        status=doc.status or "INDEXED",
        memory_item_id=doc.memory_item_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.post("/{tenant_id}/ai-agents/{agent_id}/video-links", response_model=AgentDocumentOut, status_code=201)
async def add_agent_video_link(
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    data: AddVideoLinkIn,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI Ajanına izleyerek ve dinleyerek öğrenmesi için YouTube / Online Video linki tanımlar.
    Video transkriptini, kanalını ve altyazılarını çıkararak ajanın hafızasına (Qdrant & MemoryItem) kaydeder.
    """
    await _get_tenant_or_404(db, tenant_id)
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI Ajan bulunamadı.")
    await ensure_document_quota(db, await entitlements(db, await _get_tenant_or_404(db, tenant_id), current), tenant_id, agent_id, 0)

    if not data.url or not data.url.strip():
        raise HTTPException(status_code=400, detail="Video URL'si boş olamaz.")

    try:
        video_data = await fetch_youtube_content(data.url)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"YouTube video işleme hatası: {e}")
        raise HTTPException(status_code=400, detail=f"Video bilgisi veya transkripti alınamadı: {str(e)}")

    video_url = video_data["url"]
    video_title = (data.title.strip() if data.title and data.title.strip() else video_data["title"]) or f"YouTube Video ({video_data['video_id']})"
    extracted_text = video_data["combined_text"]
    content_size = len(extracted_text.encode("utf-8"))
    summary_text = f"🎥 Video: {video_title} (Kanal: {video_data['author']})\nURL: {video_url}\n{extracted_text[:250]}..."

    # 1. Kolektif Hafıza (MemoryItem)
    memory_item = MemoryItem(
        tenant_id=tenant_id,
        scope="AGENT",
        agent_id=agent_id,
        source_reference=video_url,
        content=extracted_text[:20000],
        metadata_json={
            "source_type": "youtube",
            "url": video_url,
            "video_id": video_data["video_id"],
            "title": video_title,
            "author": video_data["author"],
            "agent_name": agent.display_name
        },
        status="APPROVED",
        confidence_score=1.0
    )
    db.add(memory_item)
    await db.flush()

    # 2. Qdrant Vektör Hafızası
    try:
        from app.services.collective_memory import collective_memory
        point = await collective_memory.add_memory(
            tenant_id=str(tenant_id),
            scope="AGENT",
            agent_id=str(agent_id),
            source_reference=video_url,
            content=extracted_text[:10000],
            metadata={
                "source_type": "youtube",
                "url": video_url,
                "video_id": video_data["video_id"],
                "title": video_title,
                "author": video_data["author"],
                "agent_name": agent.display_name,
                "memory_item_id": str(memory_item.id)
            }
        )
        memory_item.qdrant_point_id = uuid.UUID(str(point["point_id"]))  # geri alma/terfi aynı vektörü kullanır (ADIM 8.4)
    except Exception as e:
        logger.warning(f"Qdrant video hafıza indeksleme uyarısı: {e}")

    # 3. AgentDocument Kaydı
    doc = AgentDocument(
        tenant_id=tenant_id,
        agent_id=agent_id,
        file_name=f"youtube_{video_data['video_id']}",
        original_name=video_title,
        file_type="youtube",
        file_size=content_size,
        storage_path=video_url,
        extracted_text=extracted_text[:100000],
        summary=summary_text,
        status="INDEXED",
        memory_item_id=memory_item.id
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    preview = doc.extracted_text[:400] + ("..." if len(doc.extracted_text) > 400 else "")
    return AgentDocumentOut(
        id=doc.id,
        tenant_id=doc.tenant_id,
        agent_id=doc.agent_id,
        file_name=doc.file_name,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        storage_path=doc.storage_path,
        extracted_text_preview=preview,
        summary=doc.summary,
        status=doc.status or "INDEXED",
        memory_item_id=doc.memory_item_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


class DeepSearchIn(BaseModel):
    query: str = Field(..., description="Araştırılacak konu veya pazar sorgusu")
    model_code: Optional[str] = Field(None, description="Araştırma ve sentez modeli (boşsa personelin modeli)")


@router.post("/{tenant_id}/ai-agents/{agent_id}/deep-search")
async def trigger_agent_deep_search(
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    data: DeepSearchIn,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI Ajanı için internette çoklu kaynaklı Deep Search araştırması yürütür.
    Bulguları sentezler, kalıcı bilgi maddeleri olarak ajanın hafızasına kaydeder
    ve araştırma raporunu kütüphaneye ekler.
    """
    await _get_tenant_or_404(db, tenant_id)
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI Ajan bulunamadı.")
    await ensure_document_quota(db, await entitlements(db, await _get_tenant_or_404(db, tenant_id), current), tenant_id, agent_id, 0)

    if not data.query or not data.query.strip():
        raise HTTPException(status_code=400, detail="Araştırma konusu boş olamaz.")

    try:
        from app.services.agent_learning_service import agent_learning_service
        result = await agent_learning_service.deep_search_and_learn(
            tenant_id=tenant_id,
            agent_id=agent_id,
            query=data.query.strip(),
            db=db,
            model_code=data.model_code
        )
        return result
    except Exception as e:
        logger.error(f"Deep Search hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Deep Search araştırması gerçekleştirilemedi: {str(e)}")


class DeepSearchSectorTitleIn(BaseModel):
    job_title_id: uuid.UUID = Field(..., description="Ajanın ünvanı")
    agent_name: Optional[str] = Field(None, description="AI Ajan adı")
    agent_id: Optional[uuid.UUID] = Field(None, description="Mevcut ajan varsa ID'si")
    model_code: Optional[str] = Field(None, description="Model kodu (boşsa personelin modeli)")


@router.post("/{tenant_id}/ai-agents/deep-search-sector-title")
async def deep_search_sector_title_onboarding(
    tenant_id: uuid.UUID,
    data: DeepSearchSectorTitleIn,
    db: AsyncSession = Depends(get_db)
):
    """
    AI Ajanı Tanımlanırken veya Eğitilirken:
    Şirketin sektörü ve ajanın ünvanı üzerine çift odaklı Deep Search araştırması yapar.
    Sektör dinamiklerini ve ünvanın ne iş yaptığını öğrenip zenginleştirilmiş persona promptu
    ve hafıza maddeleri döner / kaydeder.
    """
    await _get_tenant_or_404(db, tenant_id)
    try:
        from app.services.agent_learning_service import agent_learning_service
        result = await agent_learning_service.deep_search_sector_and_title(
            tenant_id=tenant_id,
            job_title_id=data.job_title_id,
            db=db,
            agent_name=data.agent_name,
            agent_id=data.agent_id,
            model_code=data.model_code
        )
        return result
    except Exception as e:
        logger.error(f"Sektör & Ünvan Deep Search hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Sektör ve ünvan araştırması gerçekleştirilemedi: {str(e)}")


@router.post("/{tenant_id}/ai-agents/{agent_id}/deep-search-sector-title")
async def deep_search_sector_title_existing_agent(
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    model_code: Optional[str] = Query(None),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mevcut bir AI Ajanı için şirket sektörü ve ajanın ünvanı üzerine Deep Search yapar ve hafızasına kaydeder."""
    await _get_tenant_or_404(db, tenant_id)
    agent = await db.get(Actor, agent_id)
    if not agent or agent.tenant_id != tenant_id or agent.actor_type != "AI_AGENT":
        raise HTTPException(status_code=404, detail="AI Ajan bulunamadı.")
    await ensure_document_quota(db, await entitlements(db, await _get_tenant_or_404(db, tenant_id), current), tenant_id, agent_id, 0)
    if not agent.job_title_id:
        raise HTTPException(status_code=400, detail="Ajanın atanmış bir ünvanı bulunmuyor.")

    try:
        from app.services.agent_learning_service import agent_learning_service
        result = await agent_learning_service.deep_search_sector_and_title(
            tenant_id=tenant_id,
            job_title_id=agent.job_title_id,
            db=db,
            agent_name=agent.display_name,
            agent_id=agent.id,
            model_code=model_code
        )
        return result
    except Exception as e:
        logger.error(f"Mevcut ajan Sektör & Ünvan Deep Search hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Araştırma gerçekleştirilemedi: {str(e)}")


# Öğrenme dokümanı yükleme, listeleme, onay ve silme: app/api/v1/documents.py (ADIM 5.4)


# ==================================================================
# MADDE 6: KURUMSAL MANİFESTO DÜZENLEME VE AI ÜRETİMİ
# ==================================================================
class UpdateManifestoIn(BaseModel):
    manifesto: str = Field(..., description="Güncellenmiş Kurumsal Manifesto Metni")
    sectors: Optional[List[str]] = Field(None, description="Güncellenmiş Faaliyet Sektörleri")
    nace_codes: Optional[List[Any]] = Field(None, description="Güncellenmiş NACE Faaliyet Kodları")


@router.put("/{tenant_id}/manifesto")
async def update_company_manifesto(
    tenant_id: uuid.UUID,
    payload: UpdateManifestoIn,
    db: AsyncSession = Depends(get_db)
):
    """Şirketin kurumsal manifestosunu, sektörlerini ve NACE kodlarını doğrudan günceller ve kaydeder."""
    tenant = await _get_tenant_or_404(db, tenant_id)
    tenant.sector_manifesto = payload.manifesto.strip()
    if payload.sectors is not None:
        tenant.sectors = payload.sectors
    if payload.nace_codes is not None:
        tenant.nace_codes = payload.nace_codes
    await db.commit()
    await db.refresh(tenant)
    return {
        "success": True,
        "message": "Kurumsal manifesto, sektörler ve NACE kodları başarıyla güncellendi ve kaydedildi.",
        "sector_manifesto": tenant.sector_manifesto,
        "sectors": tenant.sectors or [],
        "nace_codes": tenant.nace_codes or []
    }


class GenerateCompanyManifestoIn(BaseModel):
    model_code: Optional[str] = Field(None, description="Seçili LLM Modeli (boşsa platform varsayılanı)")
    instructions: Optional[str] = Field(None, description="Kullanıcının Özel Düzenleme / Vurgu Talimatı")
    current_manifesto: Optional[str] = Field(None, description="Mevcut Manifesto Metni")
    sectors: Optional[List[str]] = Field(None, description="Seçili Sektörler")
    nace_codes: Optional[List[Any]] = Field(None, description="Seçili NACE Kodları")


@router.post("/{tenant_id}/generate-manifesto")
async def generate_company_manifesto(
    tenant_id: uuid.UUID,
    payload: GenerateCompanyManifestoIn,
    db: AsyncSession = Depends(get_db)
):
    """
    Şirketin seçtiği EVREN AI Modeli ile Kurumsal Manifestosunu yeniden düzenler veya üretir.
    """
    tenant = await _get_tenant_or_404(db, tenant_id)
    from app.services.manifesto_service import generate_detailed_manifesto

    effective_sectors = payload.sectors if payload.sectors is not None else (tenant.sectors or [])
    departments = [d.name for d in (await db.execute(select(Department).where(Department.tenant_id == tenant.id))).scalars()]
    titles = [t.title for t in (await db.execute(select(JobTitle).where(JobTitle.tenant_id == tenant.id))).scalars()]
    data = await generate_detailed_manifesto(
        db, tenant_id=tenant.id, company_name=tenant.name, sector_codes=effective_sectors,
        profession_codes=tenant.professions or [], website=tenant.website,
        instructions=payload.instructions, current=payload.current_manifesto or tenant.sector_manifesto,
        departments=departments, titles=titles, model_code=payload.model_code,
    )
    return {"success": True, **data}


# ==================================================================
# MADDE 1: NORMAL İNSAN KULLANICI TANIMLAMASI VE KOTA YÖNETİMİ
# ==================================================================
class CompanyUserIn(BaseModel):
    display_name: str = Field(..., description="Adı Soyadı")
    department_id: Optional[uuid.UUID] = Field(None, description="Departman ID")
    job_title_id: Optional[uuid.UUID] = Field(None, description="Ünvan ID")
    email: str = Field(..., description="Email / Kullanıcı Adı")
    password: str = Field(..., description="Kullanıcı Şifresi (En az 6 karakter)")
    status: Optional[str] = Field("ACTIVE", description="Kullanıcı Aktif/Pasif Durumu (ACTIVE veya DISABLED)")
    role_id: Optional[uuid.UUID] = Field(None, description="Sistem Yetki Rolü (Süper Yöneticinin Tanımladığı)")
    extra_permissions: Optional[List[str]] = Field(default=[], description="İzin Kataloğundan Ek İzinler")


class CompanyUserUpdateIn(BaseModel):
    display_name: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    job_title_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[uuid.UUID] = None
    extra_permissions: Optional[List[str]] = None
    daily_cost_try: Optional[float] = Field(None, ge=0, le=10_000_000)  # günlük maliyet (kişisel veri, ADIM 7.5.2)
    clear_daily_cost: bool = False


class CompanyUserOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    actor_type: str
    display_name: str
    email: Optional[str] = None
    status: str
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    job_title_id: Optional[uuid.UUID] = None
    job_title_name: Optional[str] = None
    job_title_code: Optional[str] = None
    role_id: Optional[uuid.UUID] = None
    role_name: Optional[str] = None
    role: str
    extra_permissions: List[str] = []
    effective_permissions: List[str] = []
    daily_cost_try: Optional[float] = None  # yalnızca kullanıcı yönetme yetkisi olana gösterilir (KVKK)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/{tenant_id}/user-quota")
async def get_company_user_quota(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Şirketin İnsan Kullanıcı kotası ve kullanım durumunu döner (Madde 1)."""
    tenant = await _get_tenant_or_404(db, tenant_id)
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None

    active_count_stmt = select(func.count(Actor.id)).where(
        Actor.tenant_id == tenant_id,
        Actor.actor_type == "HUMAN",
        Actor.status != "DISABLED"
    )
    active_count = (await db.execute(active_count_stmt)).scalar() or 0
    max_limit = plan.max_humans if (plan and plan.max_humans is not None) else 5

    total_count_stmt = select(func.count(Actor.id)).where(
        Actor.tenant_id == tenant_id,
        Actor.actor_type == "HUMAN"
    )
    total_count = (await db.execute(total_count_stmt)).scalar() or 0

    return {
        "active_users": active_count,
        "total_users": total_count,
        "max_users": max_limit,
        "plan_name": plan.name if plan else "Temel Paket",
        "is_limit_reached": active_count >= max_limit
    }


@router.get("/{tenant_id}/users", response_model=List[CompanyUserOut])
async def list_company_users(
    tenant_id: uuid.UUID,
    status: Optional[str] = Query(None, description="Filtre: ACTIVE, DISABLED"),
    search: Optional[str] = Query(None, description="Ad soyad veya e-posta arama"),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Şirketin insan kullanıcılarını listeler (Madde 1). Günlük maliyet yalnızca kullanıcı yönetme yetkisi olana döner (KVKK).
    Departman, Ünvan, Sistem Rolü ve İzin Kataloğu ek izinleri ile birlikte döner.
    """
    await _get_tenant_or_404(db, tenant_id)

    stmt = select(Actor).where(
        Actor.tenant_id == tenant_id,
        Actor.actor_type == "HUMAN"
    )

    if status:
        if status.upper() == "ACTIVE":
            stmt = stmt.where(Actor.status != "DISABLED")
        elif status.upper() == "DISABLED":
            stmt = stmt.where(Actor.status == "DISABLED")

    if search:
        s = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Actor.display_name).ilike(s),
                func.lower(Actor.email).ilike(s)
            )
        )

    stmt = stmt.order_by(Actor.created_at.desc())
    actors = (await db.execute(stmt)).scalars().all()

    result = []
    for a in actors:
        dept_name = None
        if a.department_id:
            dept = await db.get(Department, a.department_id)
            dept_name = dept.name if dept else None

        job_title_name = None
        job_title_code = None
        if a.job_title_id:
            jt = await db.get(JobTitle, a.job_title_id)
            if jt:
                job_title_name = jt.title
                job_title_code = jt.code

        role_name = None
        role_perms = []
        if a.role_id:
            r = await db.get(TenantRole, a.role_id)
            if r:
                role_name = r.name
                role_perms = r.permissions or []

        extra_p = a.extra_permissions or []
        effective_p = list(set(role_perms + extra_p))

        result.append(CompanyUserOut(
            daily_cost_try=float(a.daily_cost_try) if a.daily_cost_try is not None and current.has("user:manage") else None,
            id=a.id,
            tenant_id=a.tenant_id,
            actor_type=a.actor_type,
            display_name=a.display_name,
            email=a.email,
            status=a.status,
            department_id=a.department_id,
            department_name=dept_name,
            job_title_id=a.job_title_id,
            job_title_name=job_title_name,
            job_title_code=job_title_code,
            role_id=a.role_id,
            role_name=role_name or a.role,
            role=a.role,
            extra_permissions=extra_p,
            effective_permissions=effective_p,
            created_at=a.created_at,
            updated_at=a.updated_at
        ))

    return result


def _ensure_can_grant(current: CurrentUser, permissions: List[str]) -> None:
    """Kullanıcı, kendisinde olmayan bir izni başkasına veremez (süper admin hariç)."""
    if current.is_super_admin:
        return
    missing = [p for p in permissions if not current.has(p)]
    if missing:
        raise forbidden(f"Sahip olmadığınız izinleri atayamazsınız: {', '.join(sorted(set(missing)))}")


@router.post("/{tenant_id}/users", response_model=CompanyUserOut)
async def create_company_user(
    tenant_id: uuid.UUID,
    payload: CompanyUserIn,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Yeni normal insan kullanıcı tanımlaması (Madde 1).
    Paket kotası kontrolü, benzersiz e-posta, şifre hash'leme, rol ve ek izin kaydı içerir.
    """
    tenant = await _get_tenant_or_404(db, tenant_id)

    # 1. Kota Denetimi (Aktif kullanıcı olarak ekleniyorsa)
    user_status = (payload.status or "ACTIVE").upper()
    if user_status not in ("ACTIVE", "DISABLED"):
        user_status = "ACTIVE"

    if user_status != "DISABLED":
        plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
        if plan and plan.max_humans is not None:
            active_count_stmt = select(func.count(Actor.id)).where(
                Actor.tenant_id == tenant_id,
                Actor.actor_type == "HUMAN",
                Actor.status != "DISABLED"
            )
            active_count = (await db.execute(active_count_stmt)).scalar() or 0
            if active_count >= plan.max_humans:
                raise HTTPException(
                    status_code=403,
                    detail=f"Satın aldığınız '{plan.name}' paketinin azami İnsan Kullanıcı kotası ({plan.max_humans} Kullanıcı) dolmuştur. Yeni bir kullanıcı tanımlayamazsınız. Lütfen paketinizi yükseltin veya mevcut bir kullanıcıyı pasife alın."
                )

    # 2. Ad Soyad Kontrolü
    name = (payload.display_name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Kullanıcı adı soyadı boş bırakılamaz.")

    # 3. Email Kontrolü ve Benzersizlik
    email = (payload.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Geçerli bir e-posta adresi giriniz.")

    existing_email = await db.execute(
        select(Actor.id).where(func.lower(Actor.email) == email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"'{email}' e-posta adresine sahip bir kullanıcı zaten kayıtlı.")

    # 4. Şifre Kontrolü
    raw_pass = (payload.password or "").strip()
    if len(raw_pass) < 6:
        raise HTTPException(status_code=422, detail="Şifre en az 6 karakter uzunluğunda olmalıdır.")
    pwd_hash = hash_password(raw_pass)

    # 5. Departman Kontrolü
    dept_name = None
    if payload.department_id:
        dept = await db.get(Department, payload.department_id)
        if not dept or dept.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Seçilen departman bulunamadı veya bu şirkete ait değil.")
        dept_name = dept.name

    # 6. Ünvan Kontrolü
    job_title_name = None
    job_title_code = None
    if payload.job_title_id:
        jt = await db.get(JobTitle, payload.job_title_id)
        if not jt or (jt.tenant_id is not None and jt.tenant_id != tenant_id):
            raise HTTPException(status_code=404, detail="Seçilen ünvan bulunamadı veya bu şirkete ait değil.")
        job_title_name = jt.title
        job_title_code = jt.code

    # 7. Sistem Yetki Rolü Kontrolü
    role_name = "MEMBER"
    role_perms = []
    if payload.role_id:
        r = await db.get(TenantRole, payload.role_id)
        if not r or (r.tenant_id is not None and r.tenant_id != tenant_id):
            raise HTTPException(status_code=404, detail="Seçilen sistem yetki rolü bulunamadı.")
        role_name = r.name
        role_perms = r.permissions or []

    # 8. Ek İzinler
    extra_p = payload.extra_permissions or []
    _ensure_can_grant(current, list(role_perms) + list(extra_p))

    user = Actor(
        tenant_id=tenant_id,
        actor_type="HUMAN",
        display_name=name,
        email=email,
        password_hash=pwd_hash,
        role=role_name,
        role_id=payload.role_id,
        job_title_id=payload.job_title_id,
        department_id=payload.department_id,
        status=user_status,
        extra_permissions=extra_p,
        hired_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    effective_p = list(set(role_perms + extra_p))

    return CompanyUserOut(
        daily_cost_try=float(user.daily_cost_try) if user.daily_cost_try is not None else None,
        id=user.id,
        tenant_id=user.tenant_id,
        actor_type=user.actor_type,
        display_name=user.display_name,
        email=user.email,
        status=user.status,
        department_id=user.department_id,
        department_name=dept_name,
        job_title_id=user.job_title_id,
        job_title_name=job_title_name,
        job_title_code=job_title_code,
        role_id=user.role_id,
        role_name=role_name,
        role=user.role,
        extra_permissions=extra_p,
        effective_permissions=effective_p,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/{tenant_id}/users/{user_id}", response_model=CompanyUserOut)
async def update_company_user(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: CompanyUserUpdateIn,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Şirket kullanıcısını günceller (Madde 1).
    Durum aktif edilirse kota denetimi yapılır. Opsiyonel şifre güncelleme desteklenir.
    """
    tenant = await _get_tenant_or_404(db, tenant_id)
    user = await db.get(Actor, user_id)
    if not user or user.tenant_id != tenant_id or user.actor_type != "HUMAN":
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    if payload.clear_daily_cost:
        user.daily_cost_try = None
    elif payload.daily_cost_try is not None:
        user.daily_cost_try = payload.daily_cost_try

    # Durum değişikliği kontrolü (Pasiften aktife alınıyorsa kota kontrolü)
    if payload.status is not None:
        target_status = payload.status.upper()
        if target_status not in ("ACTIVE", "DISABLED"):
            target_status = "ACTIVE"
        if user.status == "DISABLED" and target_status != "DISABLED":
            plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
            if plan and plan.max_humans is not None:
                active_count_stmt = select(func.count(Actor.id)).where(
                    Actor.tenant_id == tenant_id,
                    Actor.actor_type == "HUMAN",
                    Actor.status != "DISABLED",
                    Actor.id != user_id
                )
                active_count = (await db.execute(active_count_stmt)).scalar() or 0
                if active_count >= plan.max_humans:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Satın aldığınız '{plan.name}' paketinin azami İnsan Kullanıcı kotası ({plan.max_humans} Kullanıcı) dolmuştur. Bu kullanıcıyı aktifleştiremezsiniz. Lütfen paketinizi yükseltin veya başka bir kullanıcıyı pasife alın."
                    )
        user.status = target_status

    if payload.display_name is not None:
        name = payload.display_name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Kullanıcı adı soyadı boş bırakılamaz.")
        user.display_name = name

    if payload.email is not None:
        email = payload.email.strip().lower()
        if not email or "@" not in email:
            raise HTTPException(status_code=422, detail="Geçerli bir e-posta adresi giriniz.")
        if email != (user.email or "").lower():
            existing_email = await db.execute(
                select(Actor.id).where(func.lower(Actor.email) == email, Actor.id != user_id)
            )
            if existing_email.scalar_one_or_none():
                raise HTTPException(status_code=409, detail=f"'{email}' e-posta adresi başka bir kullanıcı tarafından kullanılmaktadır.")
            user.email = email

    if payload.password is not None and payload.password.strip():
        raw_pass = payload.password.strip()
        if len(raw_pass) < 6:
            raise HTTPException(status_code=422, detail="Yeni şifre en az 6 karakter uzunluğunda olmalıdır.")
        user.password_hash = hash_password(raw_pass)

    if payload.department_id is not None:
        if payload.department_id:
            dept = await db.get(Department, payload.department_id)
            if not dept or dept.tenant_id != tenant_id:
                raise HTTPException(status_code=404, detail="Seçilen departman bulunamadı.")
            user.department_id = payload.department_id
        else:
            user.department_id = None

    if payload.job_title_id is not None:
        if payload.job_title_id:
            jt = await db.get(JobTitle, payload.job_title_id)
            if not jt or (jt.tenant_id is not None and jt.tenant_id != tenant_id):
                raise HTTPException(status_code=404, detail="Seçilen ünvan bulunamadı.")
            user.job_title_id = payload.job_title_id
        else:
            user.job_title_id = None

    if payload.role_id is not None:
        if payload.role_id:
            r = await db.get(TenantRole, payload.role_id)
            if not r or (r.tenant_id is not None and r.tenant_id != tenant_id):
                raise HTTPException(status_code=404, detail="Seçilen yetki rolü bulunamadı.")
            _ensure_can_grant(current, r.permissions or [])
            user.role_id = payload.role_id
            user.role = r.name
        else:
            user.role_id = None

    if payload.extra_permissions is not None:
        _ensure_can_grant(current, payload.extra_permissions)
        user.extra_permissions = payload.extra_permissions

    await db.commit()
    await db.refresh(user)

    dept_name = None
    if user.department_id:
        dept = await db.get(Department, user.department_id)
        dept_name = dept.name if dept else None

    job_title_name = None
    job_title_code = None
    if user.job_title_id:
        jt = await db.get(JobTitle, user.job_title_id)
        if jt:
            job_title_name = jt.title
            job_title_code = jt.code

    role_name = None
    role_perms = []
    if user.role_id:
        r = await db.get(TenantRole, user.role_id)
        if r:
            role_name = r.name
            role_perms = r.permissions or []

    extra_p = user.extra_permissions or []
    effective_p = list(set(role_perms + extra_p))

    return CompanyUserOut(
        daily_cost_try=float(user.daily_cost_try) if user.daily_cost_try is not None else None,
        id=user.id,
        tenant_id=user.tenant_id,
        actor_type=user.actor_type,
        display_name=user.display_name,
        email=user.email,
        status=user.status,
        department_id=user.department_id,
        department_name=dept_name,
        job_title_id=user.job_title_id,
        job_title_name=job_title_name,
        job_title_code=job_title_code,
        role_id=user.role_id,
        role_name=role_name or user.role,
        role=user.role,
        extra_permissions=extra_p,
        effective_permissions=effective_p,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.delete("/{tenant_id}/users/{user_id}")
async def delete_company_user(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Şirket kullanıcısını siler (Madde 1).
    """
    await _get_tenant_or_404(db, tenant_id)
    user = await db.get(Actor, user_id)
    if not user or user.tenant_id != tenant_id or user.actor_type != "HUMAN":
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    if user.role == "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Süper Yönetici hesabı silinemez.")

    if user.role == "COMPANY_ADMIN":
        other_admins_stmt = select(func.count(Actor.id)).where(
            Actor.tenant_id == tenant_id,
            Actor.actor_type == "HUMAN",
            Actor.role == "COMPANY_ADMIN",
            Actor.id != user_id,
            Actor.status != "DISABLED"
        )
        other_admins = (await db.execute(other_admins_stmt)).scalar() or 0
        if other_admins == 0:
            raise HTTPException(
                status_code=400,
                detail="Şirketin başka aktif Şirket Yöneticisi (COMPANY_ADMIN) kalmamaktadır. Sistemi yönetebilmek için lütfen önce başka bir kullanıcıya Yönetici rolü atayınız."
            )

    await db.delete(user)
    await db.commit()
    return {"success": True, "message": f"'{user.display_name}' kullanıcısı başarıyla silindi."}


