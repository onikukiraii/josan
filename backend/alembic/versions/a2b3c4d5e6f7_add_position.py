"""message=add_position

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-03-02 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("members", sa.Column("position", sa.Integer(), nullable=False, server_default="0"))
    # 既存メンバーに id 順で position を振る
    op.execute("SET @pos := 0")
    op.execute("UPDATE members SET position = (@pos := @pos + 1) ORDER BY id")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("members", "position")
