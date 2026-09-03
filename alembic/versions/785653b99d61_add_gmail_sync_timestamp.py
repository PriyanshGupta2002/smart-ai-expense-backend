"""add gmail sync timestamp

Revision ID: 785653b99d61
Revises: bae98fce20cc
Create Date: 2026-09-03 17:19:56.118807
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "785653b99d61"
down_revision: Union[str, Sequence[str], None] = "bae98fce20cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "google_connections",
        sa.Column(
            "last_gmail_sync_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "google_connections",
        "last_gmail_sync_at",
    )
