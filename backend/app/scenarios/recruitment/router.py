from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.request_context import get_request_id
from app.core.schemas import SuccessResponse
from app.core.security import get_caller_system, require_internal_token
from app.db.session import get_db_session
from app.infrastructure.llm.client import LlmClient
from app.infrastructure.llm.dependencies import get_llm_client
from app.scenarios.recruitment.schemas import (
    InterviewKitRequest,
    InterviewKitResult,
    ResumeParseRequest,
    ResumeParseResult,
    ScreeningRequest,
    ScreeningResult,
)
from app.scenarios.recruitment.service import RecruitmentService

router = APIRouter(
    prefix="/recruitment",
    tags=["招聘助手"],
    dependencies=[Depends(require_internal_token)],
)


@router.post("/resumes/parse", response_model=SuccessResponse[ResumeParseResult])
async def parse_resume(
    payload: ResumeParseRequest,
    caller_system: str = Depends(get_caller_system),
    session: AsyncSession = Depends(get_db_session),
    llm_client: LlmClient = Depends(get_llm_client),
    settings: Settings = Depends(get_settings),
) -> SuccessResponse[ResumeParseResult]:
    request_id = get_request_id()
    data = await RecruitmentService().parse_resume(
        session=session,
        llm_client=llm_client,
        request_id=request_id,
        caller_system=caller_system,
        model=settings.gptsapi_model,
        payload=payload,
    )
    return SuccessResponse(request_id=request_id, data=data)


@router.post("/screenings/evaluate", response_model=SuccessResponse[ScreeningResult])
async def evaluate_screening(
    payload: ScreeningRequest,
    caller_system: str = Depends(get_caller_system),
    session: AsyncSession = Depends(get_db_session),
    llm_client: LlmClient = Depends(get_llm_client),
    settings: Settings = Depends(get_settings),
) -> SuccessResponse[ScreeningResult]:
    request_id = get_request_id()
    data = await RecruitmentService().evaluate_screening(
        session=session,
        llm_client=llm_client,
        request_id=request_id,
        caller_system=caller_system,
        model=settings.gptsapi_model,
        payload=payload,
    )
    return SuccessResponse(request_id=request_id, data=data)


@router.post("/interview-kits/generate", response_model=SuccessResponse[InterviewKitResult])
async def generate_interview_kit(
    payload: InterviewKitRequest,
    caller_system: str = Depends(get_caller_system),
    session: AsyncSession = Depends(get_db_session),
    llm_client: LlmClient = Depends(get_llm_client),
    settings: Settings = Depends(get_settings),
) -> SuccessResponse[InterviewKitResult]:
    request_id = get_request_id()
    data = await RecruitmentService().generate_interview_kit(
        session=session,
        llm_client=llm_client,
        request_id=request_id,
        caller_system=caller_system,
        model=settings.gptsapi_model,
        payload=payload,
    )
    return SuccessResponse(request_id=request_id, data=data)
