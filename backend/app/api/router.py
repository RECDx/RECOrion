from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.models import router as models_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.actors import router as actors_router
from app.api.v1.projects import router as projects_router
from app.api.v1.chat import router as chat_router
from app.api.v1.memory import router as memory_router
from app.api.v1.auth import router as auth_router
from app.api.v1.system import router as system_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(tenants_router)
api_router.include_router(actors_router)
api_router.include_router(projects_router)
api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(auth_router)
api_router.include_router(system_router)
