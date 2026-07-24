"""create AI request and upstream attempt audit tables

Revision ID: 20260724_001
Revises:
Create Date: 2026-07-24
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_request_audit",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("request_id", sa.String(96), nullable=False),
        sa.Column("business_code", sa.String(64), nullable=False),
        sa.Column("capability_code", sa.String(128), nullable=False),
        sa.Column("caller_system", sa.String(64), nullable=False),
        sa.Column("interface_path", sa.String(255), nullable=False),
        sa.Column("request_mode", sa.String(16), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("upstream_call_count", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("request_content_hash", sa.String(64), nullable=False),
        sa.Column("request_content_length", sa.Integer(), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("ix_ai_request_audit_request_id", "ai_request_audit", ["request_id"])
    op.create_index("ix_ai_request_audit_created_at", "ai_request_audit", ["created_at"])
    op.create_index(
        "ix_ai_request_audit_created_status", "ai_request_audit", ["created_at", "status"]
    )
    op.create_index(
        "ix_ai_request_audit_business_capability",
        "ai_request_audit",
        ["business_code", "capability_code"],
    )

    op.create_table(
        "ai_upstream_attempt",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(96),
            sa.ForeignKey("ai_request_audit.request_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("attempt_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("retryable", sa.Boolean(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_upstream_attempt_request_id", "ai_upstream_attempt", ["request_id"])
    op.create_index(
        "ix_ai_upstream_attempt_request_no",
        "ai_upstream_attempt",
        ["request_id", "attempt_no"],
    )


def downgrade() -> None:
    op.drop_table("ai_upstream_attempt")
    op.drop_table("ai_request_audit")
