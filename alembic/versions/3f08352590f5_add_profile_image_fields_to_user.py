"""add profile image fields to user

Revision ID: 3f08352590f5
Revises: 37eb36103815
Create Date: 2026-08-14 16:18:08.990768

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3f08352590f5"
down_revision: Union[str, Sequence[str], None] = "37eb36103815"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column("profile_image_url", sa.String(), nullable=True),
    )

    op.add_column(
        "users",
        sa.Column("profile_image_file_id", sa.String(), nullable=True),
    )

    op.add_column(
        "users",
        sa.Column("profile_image_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("users", "profile_image_path")

    op.drop_column("users", "profile_image_file_id")

    op.drop_column("users", "profile_image_url")
