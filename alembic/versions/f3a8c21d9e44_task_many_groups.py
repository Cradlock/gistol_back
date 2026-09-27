"""bind situation tasks to many groups

Revision ID: f3a8c21d9e44
Revises: c8f2a91b4e10
Create Date: 2026-09-27 21:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a8c21d9e44"
down_revision: Union[str, Sequence[str], None] = "c8f2a91b4e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "situation_task_groups",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["situations_task.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", "group_id"),
    )
    op.execute(
        """
        INSERT INTO situation_task_groups (task_id, group_id)
        SELECT id, group_id FROM situations_task
        WHERE group_id IS NOT NULL
        """
    )
    op.drop_constraint(
        "fk_situations_task_group_id",
        "situations_task",
        type_="foreignkey",
    )
    op.drop_index("ix_situations_task_group_id", table_name="situations_task")
    op.drop_column("situations_task", "group_id")


def downgrade() -> None:
    op.add_column(
        "situations_task",
        sa.Column("group_id", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE situations_task AS task
        SET group_id = link.group_id
        FROM (
            SELECT DISTINCT ON (task_id) task_id, group_id
            FROM situation_task_groups
            ORDER BY task_id, group_id
        ) AS link
        WHERE task.id = link.task_id
        """
    )
    op.execute("DELETE FROM situations_task WHERE group_id IS NULL")
    op.alter_column("situations_task", "group_id", nullable=False)
    op.create_index(
        "ix_situations_task_group_id",
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
    op.drop_table("situation_task_groups")
