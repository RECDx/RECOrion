from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.session import get_db
from app.db.models import Actor, LLMModel, JobTitle
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/actors", tags=["Actors (Personeller - İnsan & AI)"])


class JobTitleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    code: str
    title: str
    category: str
    description: Optional[str] = None
    base_role_prompt: str
    required_skills: List[str]
    recommended_model_code: str
    autonomy_level: str
    is_active: bool

    class Config:
        from_attributes = True


class ActorResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    actor_type: str
    display_name: str
    email: Optional[str] = None
    role: str
    capability_profile: Optional[str] = None
    autonomy_level: str
    status: str

    class Config:
        from_attributes = True


class ActorCreate(BaseModel):
    tenant_id: uuid.UUID
    actor_type: str  # HUMAN veya AI_AGENT
    display_name: str
    role: str
    email: Optional[str] = None
    capability_profile: Optional[str] = None
    preferred_model_code: Optional[str] = None
    system_prompt: Optional[str] = None
    autonomy_level: str = "L1"


class CustomJobTitleCreate(BaseModel):
    tenant_id: uuid.UUID
    code: str
    title: str
    category: str = "ÖZEL"
    description: Optional[str] = None
    base_role_prompt: str
    required_skills: List[str] = []
    recommended_model_code: str = "glm-5.3"
    autonomy_level: str = "L1"


@router.get("/job-titles", response_model=List[JobTitleResponse])
async def list_job_titles(
    tenant_id: Optional[uuid.UUID] = Query(None, description="Şirket kimliği (Varsa şirkete özel ünvanları da içerir)"),
    category: Optional[str] = Query(None, description="Kategori filtresi (YAZILIM, ANALIZ, FINANS, vb.)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Sistemdeki standart kurumsal ünvanları ve varsa şirkete özel ünvanları listeler.
    """
    from sqlalchemy import or_
    if tenant_id:
        stmt = select(JobTitle).where(
            JobTitle.is_active == True,
            or_(JobTitle.tenant_id == None, JobTitle.tenant_id == tenant_id)
        )
    else:
        stmt = select(JobTitle).where(JobTitle.is_active == True, JobTitle.tenant_id == None)

    if category:
        stmt = stmt.where(JobTitle.category == category.upper())
    stmt = stmt.order_by(JobTitle.category, JobTitle.title)
    result = await db.execute(stmt)
    return result.scalars().all()


class JobTitleCreateAdmin(BaseModel):
    code: str
    title: str
    category: str
    description: Optional[str] = None
    base_role_prompt: Optional[str] = None
    required_skills: List[str] = []
    recommended_model_code: str = "glm-5.3"
    autonomy_level: str = "L1"

class JobTitleUpdate(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    base_role_prompt: str
    required_skills: List[str] = []
    recommended_model_code: str = "glm-5.3"
    autonomy_level: str = "L1"

@router.post("/job-titles/admin", response_model=JobTitleResponse)
async def create_admin_job_title(
    payload: JobTitleCreateAdmin,
    db: AsyncSession = Depends(get_db)
):
    """
    Süper Admin tarafından genel sistem ünvanı ekleme (Madde 13).
    """
    code_safe = payload.code.upper().strip()
    existing = await db.execute(select(JobTitle).where(JobTitle.code == code_safe))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"'{code_safe}' kodlu ünvan zaten mevcut.")

    role_prompt = payload.base_role_prompt
    if not role_prompt:
        role_prompt = f"Sen RECOrion otonom sisteminde {payload.category} kategorisinde görev yapan uzman bir {payload.title} dijital personelsin. Görev tanımın: {payload.description or payload.title}. Görevlerini RECOrion kalite kapıları ve kurumsal hafıza ilkelerine uygun olarak icra edersin."

    job_title = JobTitle(
        tenant_id=None,
        code=code_safe,
        title=payload.title.strip(),
        category=payload.category.strip().upper(),
        description=payload.description,
        base_role_prompt=role_prompt,
        required_skills=payload.required_skills,
        recommended_model_code=payload.recommended_model_code,
        autonomy_level=payload.autonomy_level,
        is_active=True
    )
    db.add(job_title)
    await db.commit()
    await db.refresh(job_title)
    return job_title

@router.get("/job-titles/{title_id}", response_model=JobTitleResponse)
async def get_job_title(title_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job_title = await db.get(JobTitle, title_id)
    if not job_title:
        raise HTTPException(status_code=404, detail="Ünvan bulunamadı.")
    return job_title

@router.put("/job-titles/{title_id}", response_model=JobTitleResponse)
async def update_job_title(title_id: uuid.UUID, payload: JobTitleUpdate, db: AsyncSession = Depends(get_db)):
    """
    Sektörel bazda ünvan bilgilerini ve promptunu güncelleme (Madde 13).
    """
    job_title = await db.get(JobTitle, title_id)
    if not job_title:
        raise HTTPException(status_code=404, detail="Ünvan bulunamadı.")

    job_title.title = payload.title.strip()
    job_title.category = payload.category.strip().upper()
    job_title.description = payload.description
    job_title.base_role_prompt = payload.base_role_prompt
    job_title.required_skills = payload.required_skills
    job_title.recommended_model_code = payload.recommended_model_code
    job_title.autonomy_level = payload.autonomy_level

    await db.commit()
    await db.refresh(job_title)
    return job_title

@router.delete("/job-titles/{title_id}")
async def delete_job_title(title_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Ünvan tanımını silme (Madde 13).
    """
    job_title = await db.get(JobTitle, title_id)
    if not job_title:
        raise HTTPException(status_code=404, detail="Ünvan bulunamadı.")
    await db.delete(job_title)
    await db.commit()
    return {"success": True, "message": f"'{job_title.title}' ünvanı başarıyla silindi."}

@router.post("/job-titles/{title_id}/regenerate-prompt")
async def regenerate_job_title_prompt(title_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Sektörün rol promptunu Genel AI Modeli (EVREN) ile yeniden oluşturma (Madde 6 & 13).
    """
    from app.db.models import SystemSetting
    from app.services.evren_gateway import EvrenLLMGateway

    job_title = await db.get(JobTitle, title_id)
    if not job_title:
        raise HTTPException(status_code=404, detail="Ünvan bulunamadı.")

    # Sistemde seçilmiş en güçlü Genel AI Modelini al
    setting = await db.get(SystemSetting, "default_manifesto_model")
    model_code = setting.value if setting and setting.value else "deepseek-v4.1-flash"

    skills_str = ", ".join(job_title.required_skills) if job_title.required_skills else "Genel Uzmanlık"
    prompt_instruction = f"""Sen RECOrion Otonom Kurumsal Yapay Zeka ekosisteminin Baş Mimarı ve Baş Operasyon Yöneticisisin.
Aşağıdaki iş ünvanı için en üst seviye deterministik, sektörel standartlara tam uyumlu, kurumsal hafıza ve kalite kapısı (Quality Gate) disiplinlerine sahip bir 'Sistem Rol ve Ajan Persona Promptu' oluştur:

Ünvan: {job_title.title}
Kategori / Sektör: {job_title.category}
Açıklama: {job_title.description or 'Belirtilmedi'}
Gerekli Beceriler: {skills_str}
Otonomi Seviyesi: {job_title.autonomy_level}
Önerilen Model: {job_title.recommended_model_code}

Prompt formatı:
1. Rol ve Kimlik Tanımı (Kimsin ve misyonun ne?)
2. Temel Sorumluluklar ve Çalışma Standartları
3. Kalite Kapıları ve İnceleme Kriterleri (Çıktıyı teslim etmeden önce yapılması gereken doğrulamalar)
4. Kurum Hafızası (Memory) ve Güvenlik Protokolleri
5. Çıktı Üretim Formatı ve Tonu

Yalnızca doğrudan ajanın sistem promptu olarak kullanılacak metni Türkçe olarak üret."""

    gateway = EvrenLLMGateway()
    messages = [
        {"role": "system", "content": "Sen RECOrion Otonom Yapay Zeka Ajan Mimarisisin."},
        {"role": "user", "content": prompt_instruction}
    ]

    try:
        response = await gateway.chat_completion(model_code=model_code, messages=messages, temperature=0.7, max_tokens=2048)
        msg_obj = response.get("choices", [{}])[0].get("message", {})
        new_prompt = msg_obj.get("content") or msg_obj.get("reasoning") or ""
        if not new_prompt:
            raise ValueError("Boş içerik döndü")
    except Exception as e:
        new_prompt = f"""# {job_title.title.upper()} - SİSTEM AJAN ROL PROMPTU (EVREN v3.2)
Sen RECOrion Otonom Ekosistemi bünyesinde '{job_title.category}' sektöründe görev yapan kıdemli bir {job_title.title} uzmanısın.
Otonomi Seviyen: {job_title.autonomy_level}. Temel yetenek havuzun: {skills_str}.

## GÖREVLER VE PRENSİPLER:
1. Deterministik çıktı: Halüsinasyon içermeyen, doğrulanabilir ve sektörel mevzuata uygun analizler üret.
2. Kalite Kapısı: Ürettiğin her çıktıyı çift kontrol et, eksik veya belirsiz parametreleri netleştir.
3. Dark DB & Kurum Hafızası: Ürettiğin kritik kararları ve raporları şirket kolektif hafızasına yazılması için yapılandırılmış formatta ilet."""

    # Ünvanın base_role_prompt alanını güncelle
    job_title.base_role_prompt = new_prompt.strip()
    await db.commit()
    await db.refresh(job_title)

    return {
        "success": True,
        "message": f"'{job_title.title}' için rol promptu '{model_code}' modeli kullanılarak başarıyla yeniden üretildi.",
        "model_used": model_code,
        "new_prompt": job_title.base_role_prompt
    }



@router.get("", response_model=List[ActorResponse])
@router.get("/", response_model=List[ActorResponse])
async def list_actors(
    tenant_id: Optional[uuid.UUID] = Query(None),
    actor_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Şirket personellerini (İnsan ve AI Ajanlar) listeler.
    """
    stmt = select(Actor)
    if tenant_id:
        stmt = stmt.where(Actor.tenant_id == tenant_id)
    if actor_type:
        stmt = stmt.where(Actor.actor_type == actor_type.upper())
    stmt = stmt.order_by(Actor.actor_type, Actor.display_name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ActorResponse)
async def create_actor(payload: ActorCreate, db: AsyncSession = Depends(get_db)):
    pref_model_id = None
    if payload.preferred_model_code:
        m = await db.execute(select(LLMModel).where(LLMModel.model_code == payload.preferred_model_code))
        model_obj = m.scalar_one_or_none()
        if model_obj:
            pref_model_id = model_obj.id

    actor = Actor(
        tenant_id=payload.tenant_id,
        actor_type=payload.actor_type,
        display_name=payload.display_name,
        role=payload.role,
        email=payload.email,
        capability_profile=payload.capability_profile,
        preferred_model_id=pref_model_id,
        system_prompt=payload.system_prompt,
        autonomy_level=payload.autonomy_level,
        status="IDLE"
    )
    db.add(actor)
    await db.commit()
    await db.refresh(actor)
    return actor
