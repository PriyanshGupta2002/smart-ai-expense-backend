"""update receipt schema

Revision ID: bae98fce20cc
Revises: 88a6477f5fe9
Create Date: 2026-09-03 16:44:23.503272
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "bae98fce20cc"
down_revision: Union[str, Sequence[str], None] = "88a6477f5fe9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Gmail / import source
    op.add_column(
        "receipts",
        sa.Column(
            "source",
            sa.String(length=30),
            nullable=False,
            server_default="UPLOAD",
        ),
    )

    # Gmail message ID used for deduplication
    op.add_column(
        "receipts",
        sa.Column(
            "gmail_message_id",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # Gmail transactions don't have receipt images
    op.alter_column(
        "receipts",
        "imagekit_file_id",
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
    )

    op.alter_column(
        "receipts",
        "image_url",
        existing_type=sa.TEXT(),
        nullable=True,
    )

    # Prevent importing the same Gmail message twice
    op.create_index(
        "ix_receipts_gmail_message_id",
        "receipts",
        ["gmail_message_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_receipts_gmail_message_id",
        table_name="receipts",
    )

    op.alter_column(
        "receipts",
        "image_url",
        existing_type=sa.TEXT(),
        nullable=False,
    )

    op.alter_column(
        "receipts",
        "imagekit_file_id",
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
    )

    op.drop_column(
        "receipts",
        "gmail_message_id",
    )

    op.drop_column(
        "receipts",
        "source",
    )
