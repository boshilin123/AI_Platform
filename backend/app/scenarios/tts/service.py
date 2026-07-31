from sqlalchemy.ext.asyncio import AsyncSession

from app.capabilities.speech_synthesis.service import SpeechSynthesisCapability
from app.core.error_codes import ErrorCode
from app.core.errors import AppError
from app.infrastructure.speech.client import SpeechClient
from app.infrastructure.speech.models import (
    SpeechRequest,
    SpeechResponse,
    SpeechStreamingResult,
)
from app.scenarios.tts.schemas import SpeechSynthesisRequest
from app.scenarios.tts.text_segmenter import SpeechTextSegmenter


class TtsService:
    def __init__(
        self,
        capability: SpeechSynthesisCapability | None = None,
        segmenter: SpeechTextSegmenter | None = None,
    ) -> None:
        self.capability = capability or SpeechSynthesisCapability()
        self.segmenter = segmenter or SpeechTextSegmenter()

    async def synthesize(
        self,
        *,
        session: AsyncSession,
        speech_client: SpeechClient,
        request_id: str,
        caller_system: str,
        model: str,
        max_input_chars: int,
        payload: SpeechSynthesisRequest,
    ) -> SpeechResponse:
        if len(payload.text) > max_input_chars:
            raise AppError(
                ErrorCode.INVALID_REQUEST,
                f"合成文本不能超过 {max_input_chars} 个字符",
                422,
                False,
            )
        return await self.capability.execute(
            session=session,
            speech_client=speech_client,
            request_id=request_id,
            caller_system=caller_system,
            interface_path="/api/v1/tts/synthesize",
            business_code="tts",
            capability_code="tts.speech.synthesize",
            request=SpeechRequest(
                text=payload.text,
                model=model,
                voice=payload.voice,
                response_format=payload.response_format,
                speed=payload.speed,
            ),
        )

    async def stream(
        self,
        *,
        session: AsyncSession,
        speech_client: SpeechClient,
        request_id: str,
        caller_system: str,
        model: str,
        max_segment_chars: int,
        max_stream_chars: int,
        first_segment_chars: int,
        following_segment_chars: int,
        payload: SpeechSynthesisRequest,
    ) -> SpeechStreamingResult:
        if payload.response_format != "mp3":
            raise AppError(
                ErrorCode.INVALID_REQUEST,
                "流式播放当前仅支持 MP3 格式",
                422,
                False,
            )
        if len(payload.text) > max_stream_chars:
            raise AppError(
                ErrorCode.INVALID_REQUEST,
                f"流式合成文本不能超过 {max_stream_chars} 个字符",
                422,
                False,
            )

        segments = self.segmenter.split_for_streaming(
            payload.text,
            first_max_chars=min(first_segment_chars, max_segment_chars),
            following_max_chars=min(following_segment_chars, max_segment_chars),
        )
        requests = [
            SpeechRequest(
                text=segment,
                model=model,
                voice=payload.voice,
                response_format="mp3",
                speed=payload.speed,
            )
            for segment in segments
        ]
        return await self.capability.execute_stream(
            session=session,
            speech_client=speech_client,
            request_id=request_id,
            caller_system=caller_system,
            interface_path="/api/v1/tts/synthesize-stream",
            business_code="tts",
            capability_code="tts.speech.synthesize",
            input_text=payload.text,
            requests=requests,
        )
