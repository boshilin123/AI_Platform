from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.capabilities.executor import StructuredCapabilityExecutor
from app.infrastructure.llm.client import LlmClient
from app.scenarios.recruitment.prompts import (
    PROMPT_VERSION,
    interview_messages,
    resume_parse_messages,
    screening_messages,
)
from app.scenarios.recruitment.schemas import (
    InterviewKitRequest,
    InterviewKitResult,
    ResumeParseRequest,
    ResumeParseResult,
    ScreeningRequest,
    ScreeningResult,
)


class RecruitmentService:
    def __init__(self, executor: StructuredCapabilityExecutor | None = None) -> None:
        self.executor = executor or StructuredCapabilityExecutor()

    async def parse_resume(
        self,
        *,
        session: AsyncSession,
        llm_client: LlmClient,
        request_id: str,
        caller_system: str,
        model: str,
        payload: ResumeParseRequest,
    ) -> ResumeParseResult:
        return await self.executor.execute(
            session=session,
            llm_client=llm_client,
            request_id=request_id,
            caller_system=caller_system,
            interface_path="/api/v1/recruitment/resumes/parse",
            capability_code="recruitment.resume.parse",
            prompt_version=PROMPT_VERSION,
            model=model,
            messages=resume_parse_messages(payload.resume_text),
            input_content=payload.resume_text,
            result_type=ResumeParseResult,
        )

    async def evaluate_screening(
        self,
        *,
        session: AsyncSession,
        llm_client: LlmClient,
        request_id: str,
        caller_system: str,
        model: str,
        payload: ScreeningRequest,
    ) -> ScreeningResult:
        return await self.executor.execute(
            session=session,
            llm_client=llm_client,
            request_id=request_id,
            caller_system=caller_system,
            interface_path="/api/v1/recruitment/screenings/evaluate",
            capability_code="recruitment.screening.evaluate",
            prompt_version=PROMPT_VERSION,
            model=model,
            messages=screening_messages(payload.resume_text, payload.job_description),
            input_content=f"{payload.job_description}\n{payload.resume_text}",
            result_type=ScreeningResult,
        )

    async def generate_interview_kit(
        self,
        *,
        session: AsyncSession,
        llm_client: LlmClient,
        request_id: str,
        caller_system: str,
        model: str,
        payload: InterviewKitRequest,
    ) -> InterviewKitResult:
        return await self.executor.execute(
            session=session,
            llm_client=llm_client,
            request_id=request_id,
            caller_system=caller_system,
            interface_path="/api/v1/recruitment/interview-kits/generate",
            capability_code="recruitment.interview-kit.generate",
            prompt_version=PROMPT_VERSION,
            model=model,
            messages=interview_messages(
                payload.resume_text, payload.job_description, payload.screening_risks
            ),
            input_content=(
                f"{payload.job_description}\n{payload.resume_text}\n"
                + "\n".join(payload.screening_risks)
            ),
            result_type=InterviewKitResult,
        )
