from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True)
class LlmMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(slots=True)
class LlmRequest:
    messages: list[LlmMessage]
    model: str
    temperature: float = 0
    max_tokens: int | None = None
    response_format_json: bool = True


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: "TokenUsage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens


@dataclass(slots=True)
class UpstreamAttempt:
    attempt_no: int
    attempt_type: str
    status: str
    http_status: int | None
    error_code: str | None
    retryable: bool
    duration_ms: int
    usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass(slots=True)
class LlmResponse:
    content: str
    model: str
    usage: TokenUsage
    attempts: list[UpstreamAttempt]
