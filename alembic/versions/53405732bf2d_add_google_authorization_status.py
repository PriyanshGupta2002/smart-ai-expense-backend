"""add google authorization status

Revision ID: 53405732bf2d
Revises: 9e2820c2aefc
Create Date: 2026-09-11 12:36:15.231763

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "53405732bf2d"
down_revision: Union[str, Sequence[str], None] = "9e2820c2aefc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "google_connections",
        sa.Column(
            "authorization_status",
            sa.String(length=30),
            nullable=False,
            server_default="active",
        ),
    )

    op.alter_column(
        "google_connections",
        "authorization_status",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "google_connections",
        "authorization_status",
    )
