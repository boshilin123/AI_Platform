"""add TTS runtime configuration fields

Revision ID: 20260728_003
Revises: 20260727_002
Create Date: 2026-07-28
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260728_003"
down_revision: str | None = "20260727_002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "runtime_llm_configuration",
        sa.Column("speech_model", sa.String(128), nullable=False, server_default="tts-1"),
    )
    op.add_column(
        "admin_operation_audit",
        sa.Column("old_speech_model", sa.String(128), nullable=True),
    )
    op.add_column(
        "admin_operation_audit",
        sa.Column("new_speech_model", sa.String(128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("admin_operation_audit", "new_speech_model")
    op.drop_column("admin_operation_audit", "old_speech_model")
    op.drop_column("runtime_llm_configuration", "speech_model")
