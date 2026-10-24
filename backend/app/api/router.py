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
from app.api.v1.approvals import router as approvals_router
from app.api.v1.pricing import router as pricing_router
from app.api.v1.cost_items import router as cost_items_router
from app.api.v1.live import router as live_router
from app.api.v1.repository import router as repository_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.edge import router as edge_router
from app.api.v1.templates import router as templates_router
from app.api.v1.regulations import router as regulations_router
from app.api.v1.integration_catalog import router as integration_catalog_router
from app.api.v1.mappings import router as mappings_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.mcp_server import router as mcp_server_router
from app.api.v1.meetings import router as meetings_router
from app.api.v1.model_router import router as model_router_router
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
api_router.include_router(approvals_router)
api_router.include_router(pricing_router)
api_router.include_router(cost_items_router)
api_router.include_router(live_router)
api_router.include_router(repository_router)
api_router.include_router(dashboard_router)
api_router.include_router(integrations_router)
api_router.include_router(edge_router)
api_router.include_router(templates_router)
api_router.include_router(regulations_router)
api_router.include_router(integration_catalog_router)
api_router.include_router(mappings_router)
api_router.include_router(transfers_router)
api_router.include_router(mcp_server_router)
api_router.include_router(meetings_router)
api_router.include_router(model_router_router)
