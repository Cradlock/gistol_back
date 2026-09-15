"""exam control workflow

Revision ID: a41e8d3f6b72
Revises: 9c124af80d73
Create Date: 2026-09-15 23:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a41e8d3f6b72"
down_revision: Union[str, Sequence[str], None] = "9c124af80d73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("points", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column("questions", sa.Column("position", sa.Integer(), nullable=True))
    op.execute(
        """
        WITH ordered AS (
            SELECT id, row_number() OVER (PARTITION BY exam_id ORDER BY id) - 1 AS position
            FROM questions
        )
        UPDATE questions SET position = ordered.position
        FROM ordered WHERE questions.id = ordered.id
        """
    )
    op.alter_column(
        "questions", "position", nullable=False, server_default="0"
    )
    op.create_check_constraint(
        "ck_question_points_positive", "questions", "points >= 1"
    )
    op.create_check_constraint(
        "ck_question_position_nonnegative", "questions", "position >= 0"
    )
    op.create_unique_constraint(
        "uq_question_exam_position", "questions", ["exam_id", "position"]
    )

    op.add_column("exam_sessions", sa.Column("score", sa.Integer(), nullable=True))
    op.add_column(
        "exam_sessions",
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "exam_sessions",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_exam_session_user_exam", "exam_sessions", ["user_id", "exam_id"]
    )

    op.create_unique_constraint(
        "uq_exam_target", "exam_targets", ["exam_id", "group_id", "year"]
    )
    op.create_index(
        "uq_exam_target_whole_year",
        "exam_targets",
        ["exam_id", "year"],
        unique=True,
        postgresql_where=sa.text("group_id IS NULL"),
    )
    op.create_unique_constraint("uq_input_question", "inputs", ["question_id"])

    # Existing FK names are PostgreSQL's deterministic defaults from the initial migration.
    op.drop_constraint("questions_exam_id_fkey", "questions", type_="foreignkey")
    op.create_foreign_key(
        "questions_exam_id_fkey",
        "questions",
        "exams",
        ["exam_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("choices_question_id_fkey", "choices", type_="foreignkey")
    op.create_foreign_key(
        "choices_question_id_fkey",
        "choices",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("inputs_question_id_fkey", "inputs", type_="foreignkey")
    op.create_foreign_key(
        "inputs_question_id_fkey",
        "inputs",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("exam_targets_group_id_fkey", "exam_targets", type_="foreignkey")
    op.create_foreign_key(
        "exam_targets_group_id_fkey",
        "exam_targets",
        "groups",
        ["group_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("exam_sessions_exam_id_fkey", "exam_sessions", type_="foreignkey")
    op.create_foreign_key(
        "exam_sessions_exam_id_fkey",
        "exam_sessions",
        "exams",
        ["exam_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("exam_sessions_user_id_fkey", "exam_sessions", type_="foreignkey")
    op.create_foreign_key(
        "exam_sessions_user_id_fkey",
        "exam_sessions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "exam_session_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("choice_id", sa.Integer(), nullable=True),
        sa.Column("text", sa.String(length=1000), nullable=True),
        sa.Column("awarded_points", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(choice_id IS NULL) OR (text IS NULL)",
            name="ck_session_answer_single_value",
        ),
        sa.CheckConstraint(
            "awarded_points IS NULL OR awarded_points >= 0",
            name="ck_session_answer_awarded_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["choice_id"], ["choices.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["exam_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id", "question_id", name="uq_session_question_answer"
        ),
    )


def downgrade() -> None:
    op.drop_table("exam_session_answers")

    for table, column, target in (
        ("exam_sessions", "user_id", "users"),
        ("exam_sessions", "exam_id", "exams"),
        ("exam_targets", "group_id", "groups"),
        ("inputs", "question_id", "questions"),
        ("choices", "question_id", "questions"),
        ("questions", "exam_id", "exams"),
    ):
        name = f"{table}_{column}_fkey"
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, target, [column], ["id"])

    op.drop_constraint("uq_input_question", "inputs", type_="unique")
    op.drop_index("uq_exam_target_whole_year", table_name="exam_targets")
    op.drop_constraint("uq_exam_target", "exam_targets", type_="unique")
    op.drop_constraint(
        "uq_exam_session_user_exam", "exam_sessions", type_="unique"
    )
    op.drop_column("exam_sessions", "reviewed_at")
    op.drop_column("exam_sessions", "submitted_at")
    op.drop_column("exam_sessions", "score")
    op.drop_constraint("uq_question_exam_position", "questions", type_="unique")
    op.drop_constraint(
        "ck_question_position_nonnegative", "questions", type_="check"
    )
    op.drop_constraint(
        "ck_question_points_positive", "questions", type_="check"
    )
    op.drop_column("questions", "position")
    op.drop_column("questions", "points")
