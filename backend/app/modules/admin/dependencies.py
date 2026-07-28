from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.error_codes import ErrorCode
from app.core.errors import AppError
from app.modules.admin.service import AdminIdentity, admin_session_service

admin_bearer = HTTPBearer(auto_error=False)


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(admin_bearer),
) -> AdminIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            ErrorCode.UNAUTHORIZED,
            "需要管理员登录",
            401,
            False,
        )
    return admin_session_service.authenticate(credentials.credentials)
