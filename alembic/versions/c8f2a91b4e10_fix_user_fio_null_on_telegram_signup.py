"""allow telegram signup without name/surname

Revision ID: c8f2a91b4e10
Revises: a41e8d3f6b72
Create Date: 2026-09-16 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f2a91b4e10"
down_revision: Union[str, Sequence[str], None] = "a41e8d3f6b72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FIO_OLD = "name || ' ' || surname"
FIO_NEW = "COALESCE(name, '') || ' ' || COALESCE(surname, '')"


def upgrade() -> None:
    op.drop_index("idx_users_fio_trgm", table_name="users")
    op.drop_column("users", "fio")
    op.add_column(
        "users",
        sa.Column(
            "fio",
            sa.String(length=105),
            sa.Computed(FIO_NEW, persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_users_fio_trgm",
        "users",
        ["fio"],
        unique=False,
        postgresql_ops={"fio": "gin_trgm_ops"},
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_users_fio_trgm", table_name="users")
    op.drop_column("users", "fio")
    op.add_column(
        "users",
        sa.Column(
            "fio",
            sa.String(length=105),
            sa.Computed(FIO_OLD, persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_users_fio_trgm",
        "users",
        ["fio"],
        unique=False,
        postgresql_ops={"fio": "gin_trgm_ops"},
        postgresql_using="gin",
    )
