"""add runtime LLM configuration and admin operation audit

Revision ID: 20260727_002
Revises: 20260724_001
Create Date: 2026-07-27
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260727_002"
down_revision: str | None = "20260724_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "runtime_llm_configuration",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("base_url", sa.String(512), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("updated_by", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "admin_operation_audit",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("request_id", sa.String(96), nullable=False),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("old_base_url", sa.String(512), nullable=True),
        sa.Column("new_base_url", sa.String(512), nullable=True),
        sa.Column("old_model", sa.String(128), nullable=True),
        sa.Column("new_model", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_admin_operation_audit_request_id",
        "admin_operation_audit",
        ["request_id"],
    )
    op.create_index("ix_admin_operation_audit_actor", "admin_operation_audit", ["actor"])
    op.create_index("ix_admin_operation_audit_action", "admin_operation_audit", ["action"])
    op.create_index("ix_admin_operation_audit_status", "admin_operation_audit", ["status"])
    op.create_index(
        "ix_admin_operation_audit_created_at",
        "admin_operation_audit",
        ["created_at"],
    )
    op.create_index(
        "ix_admin_operation_audit_created_action",
        "admin_operation_audit",
        ["created_at", "action"],
    )


def downgrade() -> None:
    op.drop_table("admin_operation_audit")
    op.drop_table("runtime_llm_configuration")
