"""add paid_leave shift type and request_type column

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-02-23 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: str | Sequence[str] | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # shift_assignments.shift_type に paid_leave を追加
    op.execute(
        "ALTER TABLE shift_assignments MODIFY COLUMN shift_type "
        "ENUM('outpatient_leader','treatment_room','beauty','mw_outpatient',"
        "'ward_leader','ward','delivery','delivery_charge','ward_free','outpatient_free',"
        "'night_leader','night','day_off','paid_leave') NOT NULL"
    )

    # shift_requests に request_type カラム追加
    op.add_column(
        "shift_requests",
        sa.Column(
            "request_type",
            sa.Enum("day_off", "paid_leave", name="requesttype"),
            nullable=False,
            server_default="day_off",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("shift_requests", "request_type")

    op.execute(
        "ALTER TABLE shift_assignments MODIFY COLUMN shift_type "
        "ENUM('outpatient_leader','treatment_room','beauty','mw_outpatient',"
        "'ward_leader','ward','delivery','delivery_charge','ward_free','outpatient_free',"
        "'night_leader','night','day_off') NOT NULL"
    )
