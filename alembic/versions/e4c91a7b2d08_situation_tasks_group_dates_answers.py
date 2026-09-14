"""situation tasks bound to group with answer unique and status

Revision ID: e4c91a7b2d08
Revises: b1b73bd00c5a
Create Date: 2026-09-14 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4c91a7b2d08"
down_revision: Union[str, Sequence[str], None] = "b1b73bd00c5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

student_answer_status = sa.Enum(
    "pending",
    "positive",
    "negative",
    name="student_answer_status",
)


def upgrade() -> None:
    op.drop_table("task_targets")

    op.add_column("situations_task", sa.Column("group_id", sa.Integer(), nullable=True))
    op.add_column(
        "situations_task",
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "situations_task",
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute("DELETE FROM student_answer_task")
    op.execute("DELETE FROM situations_task")

    op.alter_column("situations_task", "group_id", nullable=False)
    op.alter_column("situations_task", "end_at", nullable=False)
    op.create_index(
        op.f("ix_situations_task_group_id"),
        "situations_task",
        ["group_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_situations_task_group_id",
        "situations_task",
        "groups",
        ["group_id"],
        ["id"],
    )
    op.drop_column("situations_task", "duration_min")
    op.alter_column("situations_task", "points", server_default=None)

    student_answer_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "student_answer_task",
        sa.Column(
            "status",
            student_answer_status,
            nullable=False,
            server_default="pending",
        ),
    )
    op.alter_column("student_answer_task", "status", server_default=None)
    op.create_unique_constraint(
        "uq_student_task_answer",
        "student_answer_task",
        ["user_id", "task_id"],
    )
    op.drop_constraint(
        "student_answer_task_task_id_fkey",
        "student_answer_task",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "student_answer_task_task_id_fkey",
        "student_answer_task",
        "situations_task",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "student_answer_task_task_id_fkey",
        "student_answer_task",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "student_answer_task_task_id_fkey",
        "student_answer_task",
        "situations_task",
        ["task_id"],
        ["id"],
    )
    op.drop_constraint("uq_student_task_answer", "student_answer_task", type_="unique")
    op.drop_column("student_answer_task", "status")
    student_answer_status.drop(op.get_bind(), checkfirst=True)

    op.add_column(
        "situations_task",
        sa.Column("duration_min", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("situations_task", "duration_min", server_default=None)
    op.drop_constraint("fk_situations_task_group_id", "situations_task", type_="foreignkey")
    op.drop_index(op.f("ix_situations_task_group_id"), table_name="situations_task")
    op.drop_column("situations_task", "points")
    op.drop_column("situations_task", "end_at")
    op.drop_column("situations_task", "group_id")

    op.create_table(
        "task_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column(
            "year",
            sa.Enum(
                "FIRST",
                "SECOND",
                "THIRD",
                "FOURTH",
                "FIFTH",
                "SIXTH",
                name="year",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(
            ["task_id"], ["situations_task.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
