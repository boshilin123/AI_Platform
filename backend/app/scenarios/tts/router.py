from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.request_context import get_request_id
from app.core.security import get_caller_system, require_internal_token
from app.db.session import get_db_session
from app.infrastructure.llm.models import LlmRuntimeConfig
from app.infrastructure.speech.client import SpeechClient
from app.infrastructure.speech.dependencies import get_speech_client
from app.modules.settings.dependencies import get_runtime_llm_config
from app.scenarios.tts.schemas import SpeechSynthesisRequest
from app.scenarios.tts.service import TtsService

router = APIRouter(
    prefix="/tts",
    tags=["文字转语音助手"],
    dependencies=[Depends(require_internal_token)],
)


@router.post(
    "/synthesize",
    response_class=Response,
    responses={
        200: {
            "description": "合成后的音频二进制",
            "content": {
                "audio/mpeg": {},
                "audio/wav": {},
            },
        }
    },
)
async def synthesize_speech(
    payload: SpeechSynthesisRequest,
    caller_system: str = Depends(get_caller_system),
    session: AsyncSession = Depends(get_db_session),
    speech_client: SpeechClient = Depends(get_speech_client),
    runtime_config: LlmRuntimeConfig = Depends(get_runtime_llm_config),
    settings: Settings = Depends(get_settings),
) -> Response:
    request_id = get_request_id()
    result = await TtsService().synthesize(
        session=session,
        speech_client=speech_client,
        request_id=request_id,
        caller_system=caller_system,
        model=runtime_config.speech_model,
        max_input_chars=settings.speech_max_input_chars,
        payload=payload,
    )
    if result.content_type in {"audio/wav", "audio/x-wav", "audio/wave"}:
        extension = "wav"
    elif result.content_type in {"audio/mpeg", "audio/mp3"}:
        extension = "mp3"
    else:
        extension = payload.response_format
    return Response(
        content=result.audio,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'inline; filename="speech-{request_id}.{extension}"',
            "X-Audio-Model": result.model,
            "X-Audio-Voice": payload.voice,
            "X-Audio-Format": extension,
            "X-Audio-Speed": f"{payload.speed:g}",
        },
    )


@router.post(
    "/synthesize-stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "分块返回的 MP3 音频；超长文本按中英文句界自动拆分",
            "content": {"audio/mpeg": {}},
        }
    },
)
async def stream_speech(
    payload: SpeechSynthesisRequest,
    caller_system: str = Depends(get_caller_system),
    session: AsyncSession = Depends(get_db_session),
    speech_client: SpeechClient = Depends(get_speech_client),
    runtime_config: LlmRuntimeConfig = Depends(get_runtime_llm_config),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    request_id = get_request_id()
    result = await TtsService().stream(
        session=session,
        speech_client=speech_client,
        request_id=request_id,
        caller_system=caller_system,
        model=runtime_config.speech_model,
        max_segment_chars=settings.speech_max_input_chars,
        max_stream_chars=settings.speech_max_stream_chars,
        payload=payload,
    )
    return StreamingResponse(
        result.chunks,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'inline; filename="speech-{request_id}.mp3"',
            "X-Audio-Model": result.model,
            "X-Audio-Voice": payload.voice,
            "X-Audio-Format": "mp3",
            "X-Audio-Speed": f"{payload.speed:g}",
            "X-Audio-Streaming": "true",
            "X-Audio-Segments": str(result.segment_count),
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )
