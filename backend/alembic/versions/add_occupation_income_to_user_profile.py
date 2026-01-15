"""add occupation and income_range to user_profile

Revision ID: add_occupation_income
Revises: add_is_confirmed_field
Create Date: 2026-01-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_occupation_income'
down_revision: Union[str, None] = 'add_is_confirmed_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add occupation and income_range columns to userprofile table"""
    op.add_column('userprofile', sa.Column('occupation', sa.String(length=100), nullable=True))
    op.add_column('userprofile', sa.Column('income_range', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Remove occupation and income_range columns from userprofile table"""
    op.drop_column('userprofile', 'income_range')
    op.drop_column('userprofile', 'occupation')
