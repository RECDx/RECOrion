"""
Paket hakları (#241): müşterinin kiralama paketine göre neleri yapabileceği.

Haklar plans.features içinde tutulur; eksik anahtarlar için güvenli (kısıtlayıcı)
varsayılanlar kullanılır. RECDx süper adminleri destek amacıyla bu sınırlara takılmaz.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.models import AgentDocument, Plan, Tenant

DEFAULTS = {
    "can_change_llm": False,
    "can_edit_role_prompt": False,
    "can_upload_title_documents": False,
    "max_documents_per_agent": 20,
    "ocr_enabled": False,
}


@dataclass
class Entitlements:
    plan_code: Optional[str]
    plan_name: Optional[str]
    can_change_llm: bool
    can_edit_role_prompt: bool
    can_create_custom_titles: bool
    can_upload_title_documents: bool
    ocr_enabled: bool
    max_documents_per_agent: int
    storage_gb: int
    allowed_models: List[str] = field(default_factory=list)
    bypass: bool = False  # süper admin

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    def model_allowed(self, model_code: str) -> bool:
        return self.bypass or not self.allowed_models or model_code.lower() in self.allowed_models


async def entitlements(db: AsyncSession, tenant: Tenant, user: Optional[CurrentUser] = None) -> Entitlements:
    plan = await db.get(Plan, tenant.plan_id) if tenant.plan_id else None
    f = {**DEFAULTS, **((plan.features if plan else None) or {})}
    bypass = bool(user and user.is_super_admin)
    return Entitlements(
        plan_code=plan.code if plan else None,
        plan_name=plan.name if plan else None,
        can_change_llm=bypass or bool(f["can_change_llm"]),
        can_edit_role_prompt=bypass or bool(f["can_edit_role_prompt"]),
        can_create_custom_titles=bypass or bool(plan and plan.can_create_custom_titles),
        can_upload_title_documents=bypass or bool(f["can_upload_title_documents"]),
        ocr_enabled=bypass or bool(f["ocr_enabled"]),
        max_documents_per_agent=int(f["max_documents_per_agent"] or 0),
        storage_gb=int((plan.storage_gb if plan else 0) or 0),
        allowed_models=[str(m).strip().lower() for m in ((plan.allowed_models if plan else None) or [])],
        bypass=bypass,
    )


def deny(message: str):
    raise HTTPException(status_code=403, detail=message)


INACTIVE_DOC_STATUSES = ("DELETED", "REJECTED", "SUPERSEDED", "FAILED")


async def ensure_document_quota(db: AsyncSession, ent: Entitlements, tenant_id, agent_id, new_bytes: int,
                                job_title_id=None) -> None:
    """Personel (veya unvan) başına doküman sayısı ve şirket depolama kotasını kontrol eder."""
    if ent.bypass:
        return
    active = AgentDocument.status.notin_(INACTIVE_DOC_STATUSES)
    owner = AgentDocument.job_title_id == job_title_id if job_title_id else AgentDocument.agent_id == agent_id
    count = (await db.execute(
        select(func.count(AgentDocument.id)).where(AgentDocument.tenant_id == tenant_id, owner, active)
    )).scalar() or 0
    if ent.max_documents_per_agent and count >= ent.max_documents_per_agent:
        deny(f"'{ent.plan_name}' paketinde bir AI personele veya unvana en fazla {ent.max_documents_per_agent} öğrenme kaynağı eklenebilir.")
    if ent.storage_gb:
        used = (await db.execute(
            select(func.coalesce(func.sum(AgentDocument.file_size), 0)).where(AgentDocument.tenant_id == tenant_id, active)
        )).scalar() or 0
        if used + new_bytes > ent.storage_gb * 1024 ** 3:
            deny(f"'{ent.plan_name}' paketinin {ent.storage_gb} GB depolama kotası doldu. Paketinizi yükseltebilir veya eski dokümanları kaldırabilirsiniz.")
