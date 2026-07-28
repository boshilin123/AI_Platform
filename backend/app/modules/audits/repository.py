from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AiRequestAudit, AiUpstreamAttempt
from app.infrastructure.llm.models import UpstreamAttempt


@dataclass(slots=True)
class AuditWrite:
    request_id: str
    business_code: str
    capability_code: str
    caller_system: str
    interface_path: str
    request_mode: str
    model: str
    status: str
    http_status: int
    error_code: str | None
    retry_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    duration_ms: int
    request_content_hash: str
    request_content_length: int
    prompt_version: str
    attempts: list[UpstreamAttempt]


class AuditRepository:
    async def create(self, session: AsyncSession, payload: AuditWrite) -> AiRequestAudit:
        audit = AiRequestAudit(
            request_id=payload.request_id,
            business_code=payload.business_code,
            capability_code=payload.capability_code,
            caller_system=payload.caller_system,
            interface_path=payload.interface_path,
            request_mode=payload.request_mode,
            model=payload.model,
            status=payload.status,
            http_status=payload.http_status,
            error_code=payload.error_code,
            retry_count=payload.retry_count,
            upstream_call_count=len(payload.attempts),
            prompt_tokens=payload.prompt_tokens,
            completion_tokens=payload.completion_tokens,
            total_tokens=payload.total_tokens,
            duration_ms=payload.duration_ms,
            request_content_hash=payload.request_content_hash,
            request_content_length=payload.request_content_length,
            prompt_version=payload.prompt_version,
        )
        session.add(audit)
        for attempt_no, attempt in enumerate(payload.attempts, start=1):
            session.add(
                AiUpstreamAttempt(
                    request_id=payload.request_id,
                    attempt_no=attempt_no,
                    attempt_type=attempt.attempt_type,
                    status=attempt.status,
                    http_status=attempt.http_status,
                    error_code=attempt.error_code,
                    retryable=attempt.retryable,
                    prompt_tokens=attempt.usage.prompt_tokens,
                    completion_tokens=attempt.usage.completion_tokens,
                    total_tokens=attempt.usage.total_tokens,
                    duration_ms=attempt.duration_ms,
                )
            )
        await session.commit()
        await session.refresh(audit)
        return audit

    async def list(
        self,
        session: AsyncSession,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        capability_code: str | None = None,
        request_id: str | None = None,
    ) -> tuple[list[AiRequestAudit], int]:
        statement: Select[tuple[AiRequestAudit]] = select(AiRequestAudit)
        count_statement = select(func.count(AiRequestAudit.id))
        filters = []
        if status:
            filters.append(AiRequestAudit.status == status)
        if capability_code:
            filters.append(AiRequestAudit.capability_code == capability_code)
        if request_id:
            filters.append(AiRequestAudit.request_id.contains(request_id))
        if filters:
            statement = statement.where(*filters)
            count_statement = count_statement.where(*filters)
        total = int((await session.scalar(count_statement)) or 0)
        rows = (
            await session.scalars(
                statement.order_by(AiRequestAudit.created_at.desc(), AiRequestAudit.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return list(rows), total

    async def list_for_export(
        self,
        session: AsyncSession,
        *,
        status: str | None = None,
        capability_code: str | None = None,
        limit: int = 5000,
    ) -> list[AiRequestAudit]:
        statement = select(AiRequestAudit)
        if status:
            statement = statement.where(AiRequestAudit.status == status)
        if capability_code:
            statement = statement.where(AiRequestAudit.capability_code == capability_code)
        return list(
            (
                await session.scalars(
                    statement.order_by(AiRequestAudit.created_at.desc()).limit(limit)
                )
            ).all()
        )

    async def summary_since(self, session: AsyncSession, since: datetime) -> dict[str, int | float]:
        row = (
            await session.execute(
                select(
                    func.count(AiRequestAudit.id),
                    func.coalesce(func.sum(AiRequestAudit.total_tokens), 0),
                    func.coalesce(func.sum(AiRequestAudit.upstream_call_count), 0),
                    func.coalesce(func.sum(AiRequestAudit.retry_count), 0),
                    func.coalesce(func.sum(AiRequestAudit.duration_ms), 0),
                    func.coalesce(
                        func.sum(case((AiRequestAudit.status == "success", 1), else_=0)),
                        0,
                    ),
                ).where(AiRequestAudit.created_at >= since)
            )
        ).one()
        count = int(row[0] or 0)
        return {
            "request_count": count,
            "total_tokens": int(row[1] or 0),
            "upstream_call_count": int(row[2] or 0),
            "retry_count": int(row[3] or 0),
            "duration_total": int(row[4] or 0),
            "success_count": int(row[5] or 0),
        }

    async def request_counts_by_intervals(
        self,
        session: AsyncSession,
        intervals: list[tuple[datetime, datetime]],
    ) -> list[int]:
        if not intervals:
            return []
        columns = [
            func.coalesce(
                func.sum(
                    case(
                        (
                            (AiRequestAudit.created_at >= start)
                            & (AiRequestAudit.created_at < end),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            )
            for start, end in intervals
        ]
        row = (await session.execute(select(*columns))).one()
        return [int(value or 0) for value in row]
