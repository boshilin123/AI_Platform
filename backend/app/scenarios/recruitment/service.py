from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.capabilities.executor import StructuredCapabilityExecutor
from app.infrastructure.llm.client import LlmClient
from app.scenarios.recruitment.file_parser import ResumeFileParser
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
    def __init__(
        self,
        executor: StructuredCapabilityExecutor | None = None,
        file_parser: ResumeFileParser | None = None,
    ) -> None:
        self.executor = executor or StructuredCapabilityExecutor()
        self.file_parser = file_parser

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
        return await self._execute_resume_parse(
            session=session,
            llm_client=llm_client,
            request_id=request_id,
            caller_system=caller_system,
            model=model,
            resume_text=payload.resume_text,
            interface_path="/api/v1/recruitment/resumes/parse",
        )

    async def parse_resume_file(
        self,
        *,
        session: AsyncSession,
        llm_client: LlmClient,
        request_id: str,
        caller_system: str,
        model: str,
        upload: UploadFile,
    ) -> ResumeParseResult:
        if self.file_parser is None:
            raise RuntimeError("ResumeFileParser must be configured for file uploads")
        parsed = await self.file_parser.parse(upload)
        return await self._execute_resume_parse(
            session=session,
            llm_client=llm_client,
            request_id=request_id,
            caller_system=caller_system,
            model=model,
            resume_text=parsed.text,
            interface_path="/api/v1/recruitment/resumes/parse-file",
            audit_content_hash=parsed.source_sha256,
            audit_content_length=parsed.source_size,
        )

    async def _execute_resume_parse(
        self,
        *,
        session: AsyncSession,
        llm_client: LlmClient,
        request_id: str,
        caller_system: str,
        model: str,
        resume_text: str,
        interface_path: str,
        audit_content_hash: str | None = None,
        audit_content_length: int | None = None,
    ) -> ResumeParseResult:
        return await self.executor.execute(
            session=session,
            llm_client=llm_client,
            request_id=request_id,
            caller_system=caller_system,
            interface_path=interface_path,
            capability_code="recruitment.resume.parse",
            prompt_version=PROMPT_VERSION,
            model=model,
            messages=resume_parse_messages(resume_text),
            input_content=resume_text,
            result_type=ResumeParseResult,
            audit_content_hash=audit_content_hash,
            audit_content_length=audit_content_length,
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
