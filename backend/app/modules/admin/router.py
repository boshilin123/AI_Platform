from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import Settings, get_settings
from app.core.request_context import get_request_id
from app.core.schemas import SuccessResponse
from app.core.security import require_internal_token
from app.modules.admin.dependencies import admin_bearer, require_admin
from app.modules.admin.schemas import (
    AdminLoginRequest,
    AdminLogoutData,
    AdminSessionData,
    AdminSessionStatus,
)
from app.modules.admin.service import AdminIdentity, admin_session_service

router = APIRouter(
    prefix="/admin",
    tags=["管理员认证"],
    dependencies=[Depends(require_internal_token)],
)


@router.post("/login", response_model=SuccessResponse[AdminSessionData])
async def login(
    payload: AdminLoginRequest,
    settings: Settings = Depends(get_settings),
) -> SuccessResponse[AdminSessionData]:
    data = await admin_session_service.login(payload, settings)
    return SuccessResponse(request_id=get_request_id(), data=data)


@router.get("/session", response_model=SuccessResponse[AdminSessionStatus])
async def read_session(
    identity: AdminIdentity = Depends(require_admin),
) -> SuccessResponse[AdminSessionStatus]:
    return SuccessResponse(
        request_id=get_request_id(),
        data=AdminSessionStatus(username=identity.username, expires_at=identity.expires_at),
    )


@router.delete("/session", response_model=SuccessResponse[AdminLogoutData])
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(admin_bearer),
    _: AdminIdentity = Depends(require_admin),
) -> SuccessResponse[AdminLogoutData]:
    logged_out = admin_session_service.logout(credentials.credentials)
    return SuccessResponse(
        request_id=get_request_id(),
        data=AdminLogoutData(logged_out=logged_out),
    )
