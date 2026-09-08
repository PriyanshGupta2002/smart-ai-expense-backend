"""update whatsapp session id

Revision ID: e5f8699d679e

Revises: 5fe39e880b81

Create Date: 2026-09-08 15:02:28.796388
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f8699d679e"
down_revision: Union[str, Sequence[str], None] = "5fe39e880b81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "whatsapp_connections",
        "session_name",
        new_column_name="session_id",
    )


def downgrade() -> None:
    op.alter_column(
        "whatsapp_connections",
        "session_id",
        new_column_name="session_name",
    )
