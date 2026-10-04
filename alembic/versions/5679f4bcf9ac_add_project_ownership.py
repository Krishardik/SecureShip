"""add project ownership

Revision ID: 5679f4bcf9ac
Revises: 2a1095fd08af
Create Date: 2026-10-04 10:49:14.485422

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5679f4bcf9ac"
down_revision: str | Sequence[str] | None = "2a1095fd08af"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add project ownership to existing and future projects."""

    # Add the column as nullable first so existing projects can be migrated.
    op.add_column(
        "projects",
        sa.Column("owner_id", sa.Integer(), nullable=True),
    )

    # Assign existing projects to the known development user.
    op.execute(sa.text("UPDATE projects SET owner_id = 1 WHERE owner_id IS NULL"))

    # Rebuild the SQLite table so owner_id can become NOT NULL
    # and the foreign-key constraint can be named explicitly.
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_projects_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_projects_owner_id",
            ["owner_id"],
            unique=False,
        )


def downgrade() -> None:
    """Remove project ownership."""

    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_index("ix_projects_owner_id")
        batch_op.drop_constraint(
            "fk_projects_owner_id_users",
            type_="foreignkey",
        )

    op.drop_column("projects", "owner_id")
