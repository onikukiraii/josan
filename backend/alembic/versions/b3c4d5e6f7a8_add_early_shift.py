"""add early_shift capability and is_early column

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # member_capabilities.capability_type に early_shift を追加
    op.execute(
        "ALTER TABLE member_capabilities MODIFY COLUMN capability_type "
        "ENUM('outpatient_leader','ward_leader','night_leader','day_shift',"
        "'night_shift','beauty','mw_outpatient','ward_staff','rookie','early_shift') NOT NULL"
    )

    # shift_assignments に is_early カラム追加
    op.add_column("shift_assignments", sa.Column("is_early", sa.Boolean(), nullable=False, server_default="0"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("shift_assignments", "is_early")

    op.execute(
        "ALTER TABLE member_capabilities MODIFY COLUMN capability_type "
        "ENUM('outpatient_leader','ward_leader','night_leader','day_shift',"
        "'night_shift','beauty','mw_outpatient','ward_staff','rookie') NOT NULL"
    )
