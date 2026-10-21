from fastapi import APIRouter, Depends
from app.api.v1.health import router as health_router
from app.api.v1.models import router as models_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.actors import router as actors_router
from app.api.v1.projects import router as projects_router
from app.api.v1.chat import router as chat_router
from app.api.v1.memory import router as memory_router
from app.api.v1.auth import router as auth_router
from app.api.v1.system import router as system_router
from app.api.v1.company import router as company_router
from app.api.v1.sectors import router as sectors_router
from app.api.v1.professions import router as professions_router
from app.api.v1.public import router as public_router
from app.api.v1.ai import router as ai_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.documents import router as documents_router
from app.api.v1.workflow import router as workflow_router
from app.core.access_policy import enforce_access_policy

# Tüm uçlar merkezi erişim politikasından geçer (app/core/access_policy.py)
api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(enforce_access_policy)])

api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(tenants_router)
api_router.include_router(actors_router)
api_router.include_router(projects_router)
api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(auth_router)
api_router.include_router(system_router)
api_router.include_router(company_router)
api_router.include_router(sectors_router)
api_router.include_router(professions_router)
api_router.include_router(public_router)
api_router.include_router(ai_router)
api_router.include_router(catalog_router)
api_router.include_router(documents_router)
api_router.include_router(workflow_router)
