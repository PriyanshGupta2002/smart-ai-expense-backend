"""add week key to notifications

Revision ID: fd77f72cc365
Revises: 53405732bf2d
Create Date: 2026-09-11 16:49:24.200209
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "fd77f72cc365"
down_revision: Union[str, Sequence[str], None] = "53405732bf2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add week key used for weekly notification idempotency.
    #
    # Example:
    #   2026-W37
    #
    # Nullable because not every notification type is weekly.
    op.add_column(
        "notifications",
        sa.Column(
            "week_key",
            sa.String(length=8),
            nullable=True,
        ),
    )

    # Useful for querying notifications by week.
    op.create_index(
        op.f("ix_notifications_week_key"),
        "notifications",
        ["week_key"],
        unique=False,
    )

    # Prevent the same user from having more than one
    # notification of the same type for the same week.
    op.create_unique_constraint(
        "uq_user_notification_week",
        "notifications",
        ["user_id", "type", "week_key"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "uq_user_notification_week",
        "notifications",
        type_="unique",
    )

    op.drop_index(
        op.f("ix_notifications_week_key"),
        table_name="notifications",
    )

    op.drop_column(
        "notifications",
        "week_key",
    )
