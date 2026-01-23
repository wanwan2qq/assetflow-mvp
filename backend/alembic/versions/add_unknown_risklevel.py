"""Add unknown to risklevel enum

Revision ID: add_unknown_risklevel
Revises: fadbbb43c01c
Create Date: 2026-01-20

This migration adds the 'unknown' value to the risklevel enum type
to match the updated Python RiskLevel enum.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_unknown_risklevel"
down_revision: str = "fadbbb43c01c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add 'UNKNOWN' value to risklevel enum."""
    # PostgreSQL requires special handling for adding values to existing enums
    # NOTE: The existing enum uses UPPERCASE values (CONSERVATIVE, MODERATE, AGGRESSIVE)
    # so we must add UNKNOWN in uppercase to match
    op.execute("ALTER TYPE risklevel ADD VALUE IF NOT EXISTS 'UNKNOWN'")


def downgrade() -> None:
    """Remove 'unknown' value from risklevel enum.
    
    Note: PostgreSQL does not allow removing values from enums directly.
    To fully downgrade, you would need to:
    1. Create a new enum without 'unknown'
    2. Update the column to use the new enum
    3. Drop the old enum
    4. Rename the new enum
    
    For simplicity, we leave the enum value in place during downgrade.
    """
    pass
