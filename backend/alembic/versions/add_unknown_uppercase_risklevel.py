"""Add UNKNOWN (uppercase) to risklevel enum

Revision ID: add_unknown_uppercase_risklevel
Revises: add_unknown_risklevel
Create Date: 2026-01-20

This migration adds the 'UNKNOWN' value (uppercase) to the risklevel enum type
to match the existing uppercase convention (CONSERVATIVE, MODERATE, AGGRESSIVE).
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_unknown_uppercase_risklevel"
down_revision: str = "add_unknown_risklevel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add 'UNKNOWN' value (uppercase) to risklevel enum."""
    # The existing enum uses UPPERCASE values: CONSERVATIVE, MODERATE, AGGRESSIVE
    # We need to add UNKNOWN in uppercase to match
    op.execute("ALTER TYPE risklevel ADD VALUE IF NOT EXISTS 'UNKNOWN'")


def downgrade() -> None:
    """Cannot remove enum values in PostgreSQL."""
    pass
