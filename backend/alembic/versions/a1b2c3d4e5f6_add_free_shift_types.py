"""add ward_free and outpatient_free shift types

Revision ID: a1b2c3d4e5f6
Revises: cf7f01cf6d0c
Create Date: 2026-02-23 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "cf7f01cf6d0c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE shift_assignments MODIFY COLUMN shift_type "
        "ENUM('outpatient_leader','treatment_room','beauty','mw_outpatient',"
        "'ward_leader','ward','delivery','delivery_charge',"
        "'ward_free','outpatient_free',"
        "'night_leader','night','day_off') NOT NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER TABLE shift_assignments MODIFY COLUMN shift_type "
        "ENUM('outpatient_leader','treatment_room','beauty','mw_outpatient',"
        "'ward_leader','ward','delivery','delivery_charge',"
        "'night_leader','night','day_off') NOT NULL"
    )
