from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.request_context import get_request_id
from app.core.schemas import SuccessResponse
from app.db.session import get_db_session
from app.modules.system.schemas import HealthData

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/health", response_model=SuccessResponse[HealthData])
async def health(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> SuccessResponse[HealthData]:
    await session.execute(text("SELECT 1"))
    return SuccessResponse(
        request_id=get_request_id(),
        data=HealthData(
            status="ok",
            service=settings.app_name,
            environment=settings.app_env,
            database="ok",
            llm_mode="mock" if settings.ai_mock_mode else "upstream",
        ),
    )
