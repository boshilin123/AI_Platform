from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from time import perf_counter
from typing import Protocol

import httpx

from app.core.config import Settings
from app.core.error_codes import ErrorCode
from app.core.errors import LlmUpstreamError
from app.infrastructure.llm.error_mapper import MappedError, map_http_error
from app.infrastructure.llm.models import (
    LlmRequest,
    LlmResponse,
    LlmRuntimeConfig,
    TokenUsage,
    UpstreamAttempt,
)


class LlmClient(Protocol):
    async def chat(self, request: LlmRequest, attempt_type: str = "primary") -> LlmResponse: ...

    async def stream(self, request: LlmRequest) -> AsyncIterator[str]: ...


class OpenAICompatibleLlmClient:
    def __init__(
        self,
        settings: Settings,
        runtime_config: LlmRuntimeConfig | None = None,
    ) -> None:
        self.settings = settings
        self.runtime_config = runtime_config or LlmRuntimeConfig(
            base_url=settings.gptsapi_base_url,
            model=settings.gptsapi_model,
            speech_model=settings.gptsapi_speech_model,
        )

    @property
    def endpoint(self) -> str:
        return f"{self.runtime_config.base_url.rstrip('/')}/chat/completions"

    async def chat(self, request: LlmRequest, attempt_type: str = "primary") -> LlmResponse:
        if not self.settings.api_key_configured:
            raise LlmUpstreamError(
                ErrorCode.UPSTREAM_AUTH_ERROR,
                "服务端尚未配置 AI API Key",
                503,
                False,
                attempts=[],
            )

        attempts: list[UpstreamAttempt] = []
        max_calls = self.settings.ai_max_retries + 1
        timeout = httpx.Timeout(
            connect=self.settings.ai_connect_timeout_seconds,
            read=self.settings.ai_read_timeout_seconds,
            write=self.settings.ai_connect_timeout_seconds,
            pool=self.settings.ai_connect_timeout_seconds,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            for call_index in range(max_calls):
                started = perf_counter()
                attempt_no = call_index + 1
                try:
                    response = await client.post(
                        self.endpoint,
                        headers={
                            "Authorization": f"Bearer {self.settings.gptsapi_api_key}",
                            "Content-Type": "application/json",
                        },
                        json=self._request_payload(request, stream=False),
                    )
                    duration_ms = int((perf_counter() - started) * 1000)
                    if response.is_success:
                        parsed: object = None
                        try:
                            parsed = response.json()
                            if not isinstance(parsed, dict):
                                raise TypeError("response root is not an object")
                            usage = self._usage_from_payload(parsed.get("usage"))
                            content = parsed["choices"][0]["message"]["content"]
                            if not isinstance(content, str):
                                raise TypeError("message content is not a string")
                        except (ValueError, KeyError, IndexError, TypeError) as exc:
                            usage_payload = parsed.get("usage") if isinstance(parsed, dict) else None
                            usage = self._usage_from_payload(usage_payload)
                            attempts.append(
                                UpstreamAttempt(
                                    attempt_no=attempt_no,
                                    attempt_type=attempt_type,
                                    status="failed",
                                    http_status=response.status_code,
                                    error_code=ErrorCode.UPSTREAM_UNAVAILABLE.value,
                                    retryable=False,
                                    duration_ms=duration_ms,
                                    usage=usage,
                                )
                            )
                            raise LlmUpstreamError(
                                ErrorCode.UPSTREAM_UNAVAILABLE,
                                "AI 上游返回结构异常",
                                502,
                                False,
                                attempts=attempts,
                            ) from exc
                        attempts.append(
                            UpstreamAttempt(
                                attempt_no=attempt_no,
                                attempt_type=attempt_type,
                                status="success",
                                http_status=response.status_code,
                                error_code=None,
                                retryable=False,
                                duration_ms=duration_ms,
                                usage=usage,
                            )
                        )
                        return LlmResponse(
                            content=content or "",
                            model=str(parsed.get("model") or request.model),
                            usage=usage,
                            attempts=attempts,
                        )

                    mapped = map_http_error(response.status_code, response.text[:1000])
                    attempts.append(
                        UpstreamAttempt(
                            attempt_no=attempt_no,
                            attempt_type=attempt_type,
                            status="failed",
                            http_status=response.status_code,
                            error_code=mapped.code.value,
                            retryable=mapped.retryable,
                            duration_ms=duration_ms,
                        )
                    )
                    if mapped.retryable and call_index < max_calls - 1:
                        await asyncio.sleep(self._retry_delay(call_index, response.headers.get("Retry-After")))
                        continue
                    raise self._upstream_error(mapped, attempts)
                except LlmUpstreamError:
                    raise
                except httpx.TimeoutException as exc:
                    duration_ms = int((perf_counter() - started) * 1000)
                    mapped = MappedError(
                        ErrorCode.UPSTREAM_TIMEOUT,
                        "AI 服务响应超时，请稍后重试",
                        504,
                        True,
                    )
                    attempts.append(
                        UpstreamAttempt(
                            attempt_no=attempt_no,
                            attempt_type=attempt_type,
                            status="failed",
                            http_status=None,
                            error_code=mapped.code.value,
                            retryable=True,
                            duration_ms=duration_ms,
                        )
                    )
                    if call_index < max_calls - 1:
                        await asyncio.sleep(self._retry_delay(call_index))
                        continue
                    raise self._upstream_error(mapped, attempts) from exc
                except httpx.RequestError as exc:
                    duration_ms = int((perf_counter() - started) * 1000)
                    mapped = MappedError(
                        ErrorCode.UPSTREAM_UNAVAILABLE,
                        "AI 上游服务暂时不可用",
                        503,
                        True,
                    )
                    attempts.append(
                        UpstreamAttempt(
                            attempt_no=attempt_no,
                            attempt_type=attempt_type,
                            status="failed",
                            http_status=None,
                            error_code=mapped.code.value,
                            retryable=True,
                            duration_ms=duration_ms,
                        )
                    )
                    if call_index < max_calls - 1:
                        await asyncio.sleep(self._retry_delay(call_index))
                        continue
                    raise self._upstream_error(mapped, attempts) from exc

        raise RuntimeError("unreachable")

    async def stream(self, request: LlmRequest) -> AsyncIterator[str]:
        if not self.settings.api_key_configured:
            raise LlmUpstreamError(
                ErrorCode.UPSTREAM_AUTH_ERROR,
                "服务端尚未配置 AI API Key",
                503,
                False,
            )
        timeout = httpx.Timeout(
            connect=self.settings.ai_connect_timeout_seconds,
            read=self.settings.ai_stream_idle_timeout_seconds,
            write=self.settings.ai_connect_timeout_seconds,
            pool=self.settings.ai_connect_timeout_seconds,
        )
        emitted = False
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self.settings.gptsapi_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=self._request_payload(request, stream=True),
                ) as response:
                    if not response.is_success:
                        body = (await response.aread()).decode(errors="replace")
                        mapped = map_http_error(response.status_code, body[:1000])
                        raise self._upstream_error(mapped, [])
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        emitted = True
                        yield f"{line}\n\n"
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            code = ErrorCode.STREAM_INTERRUPTED if emitted else ErrorCode.UPSTREAM_UNAVAILABLE
            message = "AI 流式响应中断" if emitted else "AI 上游服务暂时不可用"
            raise LlmUpstreamError(code, message, 502, not emitted) from exc

    def _request_payload(self, request: LlmRequest, stream: bool) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": request.model,
            "messages": [{"role": message.role, "content": message.content} for message in request.messages],
            "temperature": request.temperature,
            "stream": stream,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format_json and not stream:
            payload["response_format"] = {"type": "json_object"}
        if stream:
            payload["stream_options"] = {"include_usage": True}
        return payload

    def _retry_delay(self, retry_index: int, retry_after: str | None = None) -> float:
        if retry_after:
            try:
                return max(0, min(float(retry_after), 60))
            except ValueError:
                pass
        delays = self.settings.ai_retry_delays_seconds
        if not delays:
            return 0
        return max(0, delays[min(retry_index, len(delays) - 1)])

    @staticmethod
    def _usage_from_payload(payload: object) -> TokenUsage:
        if not isinstance(payload, dict):
            return TokenUsage()
        return TokenUsage(
            prompt_tokens=int(payload.get("prompt_tokens") or 0),
            completion_tokens=int(payload.get("completion_tokens") or 0),
            total_tokens=int(payload.get("total_tokens") or 0),
        )

    @staticmethod
    def _upstream_error(mapped: MappedError, attempts: list[UpstreamAttempt]) -> LlmUpstreamError:
        return LlmUpstreamError(
            mapped.code,
            mapped.message,
            mapped.public_http_status,
            mapped.retryable,
            attempts=attempts,
        )


class MockLlmClient:
    def __init__(self, model: str) -> None:
        self.model = model

    async def chat(self, request: LlmRequest, attempt_type: str = "primary") -> LlmResponse:
        await asyncio.sleep(0)
        capability = self._capability_from_messages(request)
        content = json.dumps(self._result_for(capability), ensure_ascii=False)
        usage = TokenUsage()
        return LlmResponse(
            content=content,
            model=self.model,
            usage=usage,
            attempts=[],
        )

    async def stream(self, request: LlmRequest) -> AsyncIterator[str]:
        response = await self.chat(request)
        yield f"data: {json.dumps({'content': response.content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    @staticmethod
    def _capability_from_messages(request: LlmRequest) -> str:
        system = request.messages[0].content if request.messages else ""
        if "面试" in system or "questions" in system:
            return "interview"
        if "岗位匹配" in system or "初筛" in system:
            return "screen"
        return "parse"

    @staticmethod
    def _result_for(capability: str) -> dict[str, object]:
        if capability == "screen":
            return {
                "matchScore": 84,
                "recommendation": "建议面试",
                "confidence": 0.88,
                "strengths": ["具备 Java、Python 和后端开发基础", "有 RAG 与向量数据库项目经验"],
                "risks": ["项目准确率提升缺少评估口径说明"],
                "interviewFocus": ["追问评估集构造方式", "确认检索参数与工程稳定性"],
                "finalComment": "候选人的技术方向与岗位较为匹配，建议通过面试验证项目指标。",
            }
        if capability == "interview":
            return {
                "questions": [
                    {
                        "type": "项目验真",
                        "question": "你提到项目准确率有提升，基线、测试集和指标口径分别是什么？",
                        "purpose": "验证项目指标真实性",
                    },
                    {
                        "type": "技术能力",
                        "question": "BM25 与向量检索如何融合，权重如何确定？",
                        "purpose": "验证混合检索理解",
                    },
                    {
                        "type": "工程能力",
                        "question": "模型服务超时或限流时，你会怎样设计重试和降级？",
                        "purpose": "验证工程稳定性意识",
                    },
                ]
            }
        return {
            "name": "张三",
            "school": "武汉理工大学",
            "major": "软件工程",
            "graduationTime": None,
            "skills": ["Java", "Python", "Spring Boot", "RAG", "Milvus", "Docker", "Kubernetes"],
            "projects": [
                {
                    "name": "SmartCampus 智能问答系统",
                    "summary": "使用 Spring Boot、Milvus、BM25 和大模型实现校园知识库问答",
                    "technologies": ["Spring Boot", "Milvus", "BM25", "大模型"],
                    "risks": ["准确率提升的评估方法待验证"],
                }
            ],
        }
