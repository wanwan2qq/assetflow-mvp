"""merge heads

Revision ID: 2e0176ff710f
Revises: add_memory_tracking, add_occupation_income
Create Date: 2026-01-16 15:47:22.997560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e0176ff710f'
down_revision: Union[str, None] = ('add_memory_tracking', 'add_occupation_income')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass