from __future__ import annotations

import hashlib
import json
import re
from time import perf_counter
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.errors import AppError, LlmUpstreamError
from app.infrastructure.llm.client import LlmClient
from app.infrastructure.llm.models import LlmMessage, LlmRequest, TokenUsage, UpstreamAttempt
from app.modules.audits.repository import AuditWrite
from app.modules.audits.service import AuditService

ResultT = TypeVar("ResultT", bound=BaseModel)


class StructuredCapabilityExecutor:
    def __init__(self, audit_service: AuditService | None = None) -> None:
        self.audit_service = audit_service or AuditService()

    async def execute(
        self,
        *,
        session: AsyncSession,
        llm_client: LlmClient,
        request_id: str,
        caller_system: str,
        interface_path: str,
        capability_code: str,
        prompt_version: str,
        model: str,
        messages: list[LlmMessage],
        input_content: str,
        result_type: type[ResultT],
        audit_content_hash: str | None = None,
        audit_content_length: int | None = None,
    ) -> ResultT:
        started = perf_counter()
        attempts: list[UpstreamAttempt] = []
        usage = TokenUsage()
        retry_count = 0
        actual_model = model
        try:
            primary = await llm_client.chat(
                LlmRequest(messages=messages, model=model), attempt_type="primary"
            )
            attempts.extend(primary.attempts)
            usage.add(primary.usage)
            retry_count += max(0, len(primary.attempts) - 1)
            actual_model = primary.model
            try:
                result = self._validate(primary.content, result_type)
            except (json.JSONDecodeError, ValidationError):
                repair_messages = [
                    LlmMessage(
                        role="system",
                        content=(
                            "根据原始任务输入和待修复输出，生成符合目标 Schema 的合法 JSON。"
                            "保留原始输入中可验证的信息，不得用全空字段替代已经存在的信息。"
                            "只输出 JSON，不要添加 Markdown，也不要猜测原始输入中不存在的信息。"
                            f"目标 JSON Schema：{json.dumps(result_type.model_json_schema(), ensure_ascii=False)}"
                        ),
                    ),
                    LlmMessage(
                        role="user",
                        content=(
                            f"原始任务输入：\n{input_content}\n\n"
                            f"待修复的模型输出：\n{primary.content}"
                        ),
                    ),
                ]
                repaired = await llm_client.chat(
                    LlmRequest(messages=repair_messages, model=model),
                    attempt_type="format_repair",
                )
                attempts.extend(repaired.attempts)
                usage.add(repaired.usage)
                retry_count += max(0, len(repaired.attempts) - 1)
                actual_model = repaired.model
                try:
                    result = self._validate(repaired.content, result_type)
                except (json.JSONDecodeError, ValidationError) as exc:
                    error = AppError(
                        ErrorCode.RESPONSE_FORMAT_ERROR,
                        "AI 返回结果格式异常，请稍后重试",
                        502,
                        False,
                    )
                    await self._record(
                        session=session,
                        request_id=request_id,
                        caller_system=caller_system,
                        interface_path=interface_path,
                        capability_code=capability_code,
                        prompt_version=prompt_version,
                        model=actual_model,
                        input_content=input_content,
                        audit_content_hash=audit_content_hash,
                        audit_content_length=audit_content_length,
                        attempts=attempts,
                        usage=usage,
                        retry_count=retry_count,
                        started=started,
                        status="failed",
                        http_status=error.http_status,
                        error_code=error.code.value,
                    )
                    raise error from exc

            await self._record(
                session=session,
                request_id=request_id,
                caller_system=caller_system,
                interface_path=interface_path,
                capability_code=capability_code,
                prompt_version=prompt_version,
                model=actual_model,
                input_content=input_content,
                audit_content_hash=audit_content_hash,
                audit_content_length=audit_content_length,
                attempts=attempts,
                usage=usage,
                retry_count=retry_count,
                started=started,
                status="success",
                http_status=200,
                error_code=None,
            )
            return result
        except LlmUpstreamError as error:
            attempts.extend(error.attempts)
            for attempt in error.attempts:
                usage.add(attempt.usage)
            retry_count += max(0, len(error.attempts) - 1)
            await self._record(
                session=session,
                request_id=request_id,
                caller_system=caller_system,
                interface_path=interface_path,
                capability_code=capability_code,
                prompt_version=prompt_version,
                model=actual_model,
                input_content=input_content,
                audit_content_hash=audit_content_hash,
                audit_content_length=audit_content_length,
                attempts=attempts,
                usage=usage,
                retry_count=retry_count,
                started=started,
                status="failed",
                http_status=error.http_status,
                error_code=error.code.value,
            )
            raise

    async def _record(
        self,
        *,
        session: AsyncSession,
        request_id: str,
        caller_system: str,
        interface_path: str,
        capability_code: str,
        prompt_version: str,
        model: str,
        input_content: str,
        audit_content_hash: str | None,
        audit_content_length: int | None,
        attempts: list[UpstreamAttempt],
        usage: TokenUsage,
        retry_count: int,
        started: float,
        status: str,
        http_status: int,
        error_code: str | None,
    ) -> None:
        encoded = input_content.encode("utf-8")
        content_hash = audit_content_hash or hashlib.sha256(encoded).hexdigest()
        content_length = (
            audit_content_length if audit_content_length is not None else len(input_content)
        )
        await self.audit_service.record(
            session,
            AuditWrite(
                request_id=request_id,
                business_code="recruitment",
                capability_code=capability_code,
                caller_system=caller_system,
                interface_path=interface_path,
                request_mode="non_stream",
                model=model,
                status=status,
                http_status=http_status,
                error_code=error_code,
                retry_count=retry_count,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                duration_ms=int((perf_counter() - started) * 1000),
                request_content_hash=content_hash,
                request_content_length=content_length,
                prompt_version=prompt_version,
                attempts=attempts,
            ),
        )

    @staticmethod
    def _validate(content: str, result_type: type[ResultT]) -> ResultT:
        cleaned = content.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            cleaned = fenced.group(1)
        return result_type.model_validate(json.loads(cleaned))
