from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hmac import compare_digest

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.errors import AppError
from app.modules.admin.schemas import AdminLoginRequest, AdminSessionData


@dataclass(frozen=True, slots=True)
class AdminIdentity:
    username: str
    expires_at: datetime


class AdminSessionService:
    def __init__(self) -> None:
        self._sessions: dict[str, AdminIdentity] = {}

    async def login(self, payload: AdminLoginRequest, settings: Settings) -> AdminSessionData:
        if not settings.admin_auth_configured:
            raise AppError(
                ErrorCode.ADMIN_AUTH_NOT_CONFIGURED,
                "管理员登录尚未在服务端配置",
                503,
                False,
            )

        expected_username = settings.admin_username.strip()
        expected_password = settings.admin_password.get_secret_value()
        username_matches = compare_digest(payload.username.encode(), expected_username.encode())
        password_matches = compare_digest(
            payload.password.get_secret_value().encode(),
            expected_password.encode(),
        )
        if not (username_matches and password_matches):
            await asyncio.sleep(0.2)
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "管理员账号或密码不正确",
                401,
                False,
            )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.admin_session_ttl_minutes)
        token = secrets.token_urlsafe(32)
        self._discard_expired(now)
        self._sessions[token] = AdminIdentity(username=expected_username, expires_at=expires_at)
        return AdminSessionData(
            username=expected_username,
            access_token=token,
            expires_at=expires_at,
        )

    def authenticate(self, token: str) -> AdminIdentity:
        now = datetime.now(timezone.utc)
        self._discard_expired(now)
        identity = self._sessions.get(token)
        if identity is None:
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "管理员登录已失效，请重新登录",
                401,
                False,
            )
        return identity

    def logout(self, token: str) -> bool:
        return self._sessions.pop(token, None) is not None

    def _discard_expired(self, now: datetime) -> None:
        expired = [token for token, identity in self._sessions.items() if identity.expires_at <= now]
        for token in expired:
            self._sessions.pop(token, None)


admin_session_service = AdminSessionService()
