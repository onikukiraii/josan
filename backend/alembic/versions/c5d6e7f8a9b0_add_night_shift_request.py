"""add night_shift_request to request_type enum

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-04-10 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5d6e7f8a9b0"
down_revision: str | Sequence[str] | None = "b4c5d6e7f8a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE shift_requests MODIFY COLUMN request_type "
        "ENUM('day_off','paid_leave','day_shift_request','night_shift_request') "
        "NOT NULL DEFAULT 'day_off'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE shift_requests SET request_type = 'day_off' WHERE request_type = 'night_shift_request'")
    op.execute(
        "ALTER TABLE shift_requests MODIFY COLUMN request_type "
        "ENUM('day_off','paid_leave','day_shift_request') "
        "NOT NULL DEFAULT 'day_off'"
    )
