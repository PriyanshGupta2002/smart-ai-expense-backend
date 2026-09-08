"""add whatsapp connections

Revision ID: 5fe39e880b81
Revises: 785653b99d61
Create Date: 2026-09-08 14:30:02.385475
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5fe39e880b81"

down_revision: Union[str, Sequence[str], None] = "785653b99d61"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "whatsapp_connections",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "session_name",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "phone_number",
            sa.String(length=30),
            nullable=True,
        ),
        sa.Column(
            "connected",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "connected_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("session_name"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("whatsapp_connections")
