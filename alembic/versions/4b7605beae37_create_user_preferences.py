"""create user preferences

Revision ID: 4b7605beae37
Revises: 3486a0af805c
Create Date: 2026-09-09 19:25:23.384904
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4b7605beae37"
down_revision: Union[str, Sequence[str], None] = "3486a0af805c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user preferences table."""

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "response_style",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "default_expense_period",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "default_report_format",
            sa.String(length=10),
            nullable=False,
        ),
        sa.Column(
            "confirm_before_actions",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "weekly_summary",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "monthly_summary",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "budget_alerts",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "unusual_spending_alerts",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "theme",
            sa.String(length=10),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_user_preferences_user_id",
        "user_preferences",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop user preferences table."""

    op.drop_index(
        "ix_user_preferences_user_id",
        table_name="user_preferences",
    )

    op.drop_table("user_preferences")
