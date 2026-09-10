"""make whatsapp session id nullable

Revision ID: 3486a0af805c
Revises: e5f8699d679e
Create Date: 2026-09-08 15:22:57.171257

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "3486a0af805c"
down_revision: Union[str, Sequence[str], None] = "e5f8699d679e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "whatsapp_connections",
        "session_id",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "whatsapp_connections",
        "session_id",
        existing_type=sa.String(),
        nullable=False,
    )
