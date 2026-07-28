from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

from app.infrastructure.llm.models import UpstreamAttempt

SpeechVoice = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
SpeechFormat = Literal["mp3", "wav"]


@dataclass(frozen=True, slots=True)
class SpeechRuntimeConfig:
    base_url: str
    model: str


@dataclass(slots=True)
class SpeechRequest:
    text: str
    model: str
    voice: SpeechVoice
    response_format: SpeechFormat
    speed: float


@dataclass(slots=True)
class SpeechResponse:
    audio: bytes
    content_type: str
    model: str
    attempts: list[UpstreamAttempt]


@dataclass(slots=True)
class SpeechStreamResponse:
    chunks: AsyncIterator[bytes]
    content_type: str
    model: str
    attempts: list[UpstreamAttempt]
    close_callback: Callable[[], Awaitable[None]]

    async def aclose(self) -> None:
        await self.close_callback()


@dataclass(slots=True)
class SpeechStreamingResult:
    chunks: AsyncIterator[bytes]
    content_type: str
    model: str
    segment_count: int
