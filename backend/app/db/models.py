from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AiRequestAudit(Base):
    __tablename__ = "ai_request_audit"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False, index=True)
    business_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    capability_code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    caller_system: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    interface_path: Mapped[str] = mapped_column(String(255), nullable=False)
    request_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="non_stream")
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    http_status: Mapped[int] = mapped_column(Integer, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upstream_call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )

    attempts: Mapped[list["AiUpstreamAttempt"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_ai_request_audit_created_status", "created_at", "status"),
        Index("ix_ai_request_audit_business_capability", "business_code", "capability_code"),
    )


class AiUpstreamAttempt(Base):
    __tablename__ = "ai_upstream_attempt"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    request_id: Mapped[str] = mapped_column(
        String(96), ForeignKey("ai_request_audit.request_id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_type: Mapped[str] = mapped_column(String(32), nullable=False, default="primary")
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    audit: Mapped[AiRequestAudit] = relationship(back_populates="attempts")

    __table_args__ = (Index("ix_ai_upstream_attempt_request_no", "request_id", "attempt_no"),)


class RuntimeLlmConfiguration(Base):
    __tablename__ = "runtime_llm_configuration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    speech_model: Mapped[str] = mapped_column(String(128), nullable=False, default="tts-1")
    updated_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class AdminOperationAudit(Base):
    __tablename__ = "admin_operation_audit"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    http_status: Mapped[int] = mapped_column(Integer, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    old_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    new_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    old_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    new_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    old_speech_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    new_speech_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )

    __table_args__ = (
        Index("ix_admin_operation_audit_created_action", "created_at", "action"),
    )
