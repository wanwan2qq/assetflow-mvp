"""merge_action_plan_heads

Revision ID: cf972a7df55d
Revises: a665f378fe1d, add_gin_indexes
Create Date: 2026-01-23 22:19:08.140284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf972a7df55d'
down_revision: Union[str, None] = ('a665f378fe1d', 'add_gin_indexes')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass