from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.audits.router import router as audits_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.settings.router import router as settings_router
from app.modules.system.router import router as system_router
from app.scenarios.recruitment.router import router as recruitment_router
from app.scenarios.tts.router import router as tts_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system_router)
api_router.include_router(admin_router)
api_router.include_router(dashboard_router)
api_router.include_router(recruitment_router)
api_router.include_router(tts_router)
api_router.include_router(audits_router)
api_router.include_router(settings_router)
