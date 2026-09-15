"""add answer submitted at

Revision ID: 9c124af80d73
Revises: 5b46a15f2ec0
Create Date: 2026-09-15 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c124af80d73"
down_revision: Union[str, Sequence[str], None] = "5b46a15f2ec0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "situations_task",
        sa.Column("content", sa.String(length=4000), nullable=True),
    )
    op.execute("UPDATE situations_task SET content = title WHERE content IS NULL")
    op.alter_column("situations_task", "content", nullable=False)

    op.add_column(
        "student_answer_task",
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_student_answer_task_submitted_at"),
        "student_answer_task",
        ["submitted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_student_answer_task_submitted_at"),
        table_name="student_answer_task",
    )
    op.drop_column("student_answer_task", "submitted_at")
    op.drop_column("situations_task", "content")
