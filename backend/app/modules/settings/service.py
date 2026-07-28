from __future__ import annotations

import re
from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.errors import AppError, LlmUpstreamError
from app.infrastructure.llm.catalog import (
    ModelCatalogClient,
    is_chat_model,
    is_speech_model,
)
from app.infrastructure.llm.models import LlmRuntimeConfig, UpstreamAttempt
from app.modules.settings.repository import AdminOperationAuditWrite, SettingsRepository
from app.modules.settings.schemas import (
    AdminOperationAuditItem,
    AdminOperationAuditList,
    LlmSettingsUpdate,
    ModelListData,
    SettingsData,
)

MODEL_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:/-]+$")


class SettingsService:
    def __init__(
        self,
        repository: SettingsRepository | None = None,
        catalog_client: ModelCatalogClient | None = None,
    ) -> None:
        self.repository = repository or SettingsRepository()
        self.catalog_client = catalog_client or ModelCatalogClient()

    async def effective_llm_config(
        self,
        session: AsyncSession,
        settings: Settings,
    ) -> LlmRuntimeConfig:
        row = await self.repository.get_runtime_configuration(session)
        if row is None or not self._stored_configuration_is_allowed(
            row.base_url,
            row.model,
            row.speech_model,
            settings,
        ):
            return LlmRuntimeConfig(
                base_url=settings.gptsapi_base_url.rstrip("/"),
                model=settings.gptsapi_model,
                speech_model=settings.gptsapi_speech_model,
            )
        return LlmRuntimeConfig(
            base_url=row.base_url,
            model=row.model,
            speech_model=row.speech_model,
        )

    async def read(self, session: AsyncSession, settings: Settings) -> SettingsData:
        row = await self.repository.get_runtime_configuration(session)
        if row is not None and not self._stored_configuration_is_allowed(
            row.base_url,
            row.model,
            row.speech_model,
            settings,
        ):
            row = None
        runtime = (
            LlmRuntimeConfig(
                base_url=row.base_url,
                model=row.model,
                speech_model=row.speech_model,
            )
            if row is not None
            else LlmRuntimeConfig(
                base_url=settings.gptsapi_base_url.rstrip("/"),
                model=settings.gptsapi_model,
                speech_model=settings.gptsapi_speech_model,
            )
        )
        return SettingsData(
            environment=settings.app_env,
            mock_mode=settings.ai_mock_mode,
            api_key_configured=settings.api_key_configured,
            base_url=runtime.base_url,
            model=runtime.model,
            speech_model=runtime.speech_model,
            connect_timeout_seconds=settings.ai_connect_timeout_seconds,
            read_timeout_seconds=settings.ai_read_timeout_seconds,
            stream_idle_timeout_seconds=settings.ai_stream_idle_timeout_seconds,
            max_retries=settings.ai_max_retries,
            retry_delays_seconds=settings.ai_retry_delays_seconds,
            speech_max_input_chars=settings.speech_max_input_chars,
            speech_max_stream_chars=settings.speech_max_stream_chars,
            audit_retention_days=settings.audit_retention_days,
            internal_auth_enabled=bool(settings.internal_api_token),
            admin_auth_configured=settings.admin_auth_configured,
            configuration_source="database" if row is not None else "environment",
            updated_by=row.updated_by if row is not None else None,
            updated_at=self._as_utc(row.updated_at) if row is not None else None,
        )

    async def discover_models(
        self,
        session: AsyncSession,
        settings: Settings,
        *,
        base_url: str,
        actor: str,
        request_id: str,
    ) -> ModelListData:
        normalized_url = self.validate_base_url(base_url, settings)
        try:
            result = await self.catalog_client.list_models(
                base_url=normalized_url,
                api_key=settings.gptsapi_api_key,
                connect_timeout_seconds=settings.ai_connect_timeout_seconds,
                read_timeout_seconds=settings.ai_read_timeout_seconds,
            )
        except LlmUpstreamError as error:
            attempt = error.attempts[0] if error.attempts else None
            await self.repository.record_operation(
                session,
                self._discovery_audit(
                    request_id=request_id,
                    actor=actor,
                    base_url=normalized_url,
                    status="failed",
                    http_status=attempt.http_status if attempt and attempt.http_status else error.http_status,
                    error_code=error.code.value,
                    attempt=attempt,
                ),
            )
            raise

        await self.repository.record_operation(
            session,
            self._discovery_audit(
                request_id=request_id,
                actor=actor,
                base_url=normalized_url,
                status="success",
                http_status=result.attempt.http_status or 200,
                error_code=None,
                attempt=result.attempt,
            ),
        )
        return ModelListData(
            base_url=normalized_url,
            models=result.models,
            chat_models=[model for model in result.models if is_chat_model(model)],
            speech_models=[model for model in result.models if is_speech_model(model)],
        )

    async def update_llm_settings(
        self,
        session: AsyncSession,
        settings: Settings,
        payload: LlmSettingsUpdate,
        *,
        actor: str,
        request_id: str,
    ) -> SettingsData:
        started = perf_counter()
        current = await self.effective_llm_config(session, settings)
        try:
            normalized_url = self.validate_base_url(payload.baseUrl, settings)
            model = self.validate_chat_model(payload.model)
            speech_model = self.validate_speech_model(payload.speechModel)
            catalog = await self.discover_models(
                session,
                settings,
                base_url=normalized_url,
                actor=actor,
                request_id=request_id,
            )
            if model not in catalog.models:
                raise AppError(
                    ErrorCode.MODEL_NOT_FOUND,
                    "选择的模型不在上游当前可用列表中",
                    400,
                    False,
                )
            if speech_model not in catalog.speech_models:
                raise AppError(
                    ErrorCode.MODEL_NOT_FOUND,
                    "选择的语音模型不在上游当前可用列表中",
                    400,
                    False,
                )
        except AppError as error:
            await self.repository.record_operation(
                session,
                AdminOperationAuditWrite(
                    request_id=request_id,
                    actor=actor,
                    action="settings.llm.update",
                    status="failed",
                    http_status=error.http_status,
                    error_code=error.code.value,
                    duration_ms=int((perf_counter() - started) * 1000),
                    old_base_url=current.base_url,
                    new_base_url=payload.baseUrl,
                    old_model=current.model,
                    new_model=payload.model,
                    old_speech_model=current.speech_model,
                    new_speech_model=payload.speechModel,
                ),
            )
            raise

        await self.repository.save_runtime_configuration(
            session,
            base_url=normalized_url,
            model=model,
            speech_model=speech_model,
            actor=actor,
            audit=AdminOperationAuditWrite(
                request_id=request_id,
                actor=actor,
                action="settings.llm.update",
                status="success",
                http_status=200,
                error_code=None,
                duration_ms=int((perf_counter() - started) * 1000),
                old_base_url=current.base_url,
                new_base_url=normalized_url,
                old_model=current.model,
                new_model=model,
                old_speech_model=current.speech_model,
                new_speech_model=speech_model,
            ),
        )
        return await self.read(session, settings)

    async def list_audits(
        self,
        session: AsyncSession,
        *,
        page: int,
        page_size: int,
    ) -> AdminOperationAuditList:
        rows, total = await self.repository.list_operation_audits(
            session,
            page=page,
            page_size=page_size,
        )
        return AdminOperationAuditList(
            items=[
                AdminOperationAuditItem(
                    request_id=row.request_id,
                    actor=row.actor,
                    action=row.action,
                    status=row.status,
                    http_status=row.http_status,
                    error_code=row.error_code,
                    duration_ms=row.duration_ms,
                    old_base_url=row.old_base_url,
                    new_base_url=row.new_base_url,
                    old_model=row.old_model,
                    new_model=row.new_model,
                    old_speech_model=row.old_speech_model,
                    new_speech_model=row.new_speech_model,
                    created_at=self._as_utc(row.created_at),
                )
                for row in rows
            ],
            page=page,
            page_size=page_size,
            total=total,
        )

    @staticmethod
    def validate_base_url(value: str, settings: Settings) -> str:
        try:
            parsed = urlsplit(value.strip())
            port = parsed.port
        except ValueError as exc:
            raise AppError(
                ErrorCode.INVALID_REQUEST,
                "Base URL 格式不正确",
                422,
                False,
            ) from exc
        host = (parsed.hostname or "").lower()
        allowed_hosts = {item.lower() for item in settings.gptsapi_allowed_hosts}
        path = parsed.path.rstrip("/")
        if (
            parsed.scheme.lower() != "https"
            or not host
            or host not in allowed_hosts
            or port not in (None, 443)
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or not path.endswith("/v1")
            or ".." in path.split("/")
        ):
            raise AppError(
                ErrorCode.INVALID_REQUEST,
                "Base URL 必须使用 HTTPS、受信任域名、443 端口并以 /v1 结尾",
                422,
                False,
            )
        netloc = host if port is None else f"{host}:{port}"
        return urlunsplit(("https", netloc, path, "", ""))

    @staticmethod
    def validate_model(value: str) -> str:
        model = value.strip()
        if not MODEL_ID_PATTERN.fullmatch(model):
            raise AppError(
                ErrorCode.INVALID_REQUEST,
                "模型名称格式不正确",
                422,
                False,
            )
        return model

    @classmethod
    def validate_chat_model(cls, value: str) -> str:
        model = cls.validate_model(value)
        if not is_chat_model(model):
            raise AppError(
                ErrorCode.INVALID_REQUEST,
                "文本模型不能选择语音、转写、嵌入或图片模型",
                422,
                False,
            )
        return model

    @classmethod
    def validate_speech_model(cls, value: str) -> str:
        model = cls.validate_model(value)
        if not is_speech_model(model):
            raise AppError(
                ErrorCode.INVALID_REQUEST,
                "语音模型当前仅支持 tts-1 和 tts-1-hd",
                422,
                False,
            )
        return model

    @classmethod
    def _stored_configuration_is_allowed(
        cls,
        base_url: str,
        model: str,
        speech_model: str,
        settings: Settings,
    ) -> bool:
        try:
            cls.validate_base_url(base_url, settings)
            cls.validate_chat_model(model)
            cls.validate_speech_model(speech_model)
        except AppError:
            return False
        return True

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _discovery_audit(
        *,
        request_id: str,
        actor: str,
        base_url: str,
        status: str,
        http_status: int,
        error_code: str | None,
        attempt: UpstreamAttempt | None,
    ) -> AdminOperationAuditWrite:
        return AdminOperationAuditWrite(
            request_id=request_id,
            actor=actor,
            action="settings.models.discover",
            status=status,
            http_status=http_status,
            error_code=error_code,
            duration_ms=attempt.duration_ms if attempt else 0,
            new_base_url=base_url,
        )
