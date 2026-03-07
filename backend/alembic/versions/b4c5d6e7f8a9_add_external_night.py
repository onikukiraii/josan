"""message=add_external_night

Revision ID: b4c5d6e7f8a9
Revises: a2b3c4d5e6f7
Create Date: 2026-03-02 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4c5d6e7f8a9"
down_revision: str | Sequence[str] | None = "a2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # MySQL の shifttype enum に external_night を追加
    op.execute(
        "ALTER TABLE shift_assignments MODIFY COLUMN shift_type "
        "ENUM('outpatient_leader','treatment_room','beauty','mw_outpatient',"
        "'ward_leader','ward','delivery','delivery_charge','ward_free',"
        "'outpatient_free','night_leader','night','external_night',"
        "'day_off','paid_leave') NOT NULL"
    )

    # off_days_adjustment → external_night_count
    op.add_column("members", sa.Column("external_night_count", sa.Integer(), nullable=False, server_default="0"))
    op.drop_column("members", "off_days_adjustment")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("members", sa.Column("off_days_adjustment", sa.Integer(), nullable=False, server_default="0"))
    op.drop_column("members", "external_night_count")

    # external_night を enum から削除
    op.execute(
        "ALTER TABLE shift_assignments MODIFY COLUMN shift_type "
        "ENUM('outpatient_leader','treatment_room','beauty','mw_outpatient',"
        "'ward_leader','ward','delivery','delivery_charge','ward_free',"
        "'outpatient_free','night_leader','night',"
        "'day_off','paid_leave') NOT NULL"
    )
