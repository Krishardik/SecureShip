"""baseline database schema

Revision ID: 2a1095fd08af
Revises:
Create Date: 2026-10-04 10:41:34.527413

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "2a1095fd08af"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Baseline existing database schema."""


def downgrade() -> None:
    """Baseline migration cannot be downgraded."""
