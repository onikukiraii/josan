"""add day_shift_request to request_type enum

Revision ID: e5f6a7b8c9d0
Revises: 3df37390ad99
Create Date: 2026-02-24 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "3df37390ad99"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE shift_requests MODIFY COLUMN request_type "
        "ENUM('day_off','paid_leave','day_shift_request') "
        "NOT NULL DEFAULT 'day_off'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE shift_requests SET request_type = 'day_off' WHERE request_type = 'day_shift_request'")
    op.execute(
        "ALTER TABLE shift_requests MODIFY COLUMN request_type ENUM('day_off','paid_leave') NOT NULL DEFAULT 'day_off'"
    )
