"""increase notification week key length

Revision ID: c4ceadad2fb3

Revises: fd77f72cc365

Create Date: 2026-09-11 17:03:59.691942

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.

revision: str = "c4ceadad2fb3"

down_revision: Union[str, Sequence[str], None] = "fd77f72cc365"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "notifications",
        "week_key",
        existing_type=sa.String(length=8),
        type_=sa.String(length=10),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "notifications",
        "week_key",
        existing_type=sa.String(length=10),
        type_=sa.String(length=8),
        existing_nullable=True,
    )
