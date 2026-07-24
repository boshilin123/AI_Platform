from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.request_context import get_request_id
from app.core.schemas import SuccessResponse
from app.core.security import require_internal_token
from app.modules.settings.schemas import SettingsData

router = APIRouter(
    prefix="/settings",
    tags=["基础配置"],
    dependencies=[Depends(require_internal_token)],
)


@router.get("", response_model=SuccessResponse[SettingsData])
async def read_settings(settings: Settings = Depends(get_settings)) -> SuccessResponse[SettingsData]:
    return SuccessResponse(
        request_id=get_request_id(),
        data=SettingsData(
            environment=settings.app_env,
            mock_mode=settings.ai_mock_mode,
            api_key_configured=settings.api_key_configured,
            base_url=settings.gptsapi_base_url,
            model=settings.gptsapi_model,
            connect_timeout_seconds=settings.ai_connect_timeout_seconds,
            read_timeout_seconds=settings.ai_read_timeout_seconds,
            stream_idle_timeout_seconds=settings.ai_stream_idle_timeout_seconds,
            max_retries=settings.ai_max_retries,
            retry_delays_seconds=settings.ai_retry_delays_seconds,
            audit_retention_days=settings.audit_retention_days,
            internal_auth_enabled=bool(settings.internal_api_token),
        ),
    )
