"""Phase 4: Enable pgvector extension for L3 Vector Memory

Revision ID: phase4_pgvector
Revises: cc1330024231
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'phase4_pgvector'
down_revision = 'cc1330024231'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable pgvector extension"""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')


def downgrade() -> None:
    """Disable pgvector extension"""
    # Drop pgvector extension (only if no tables are using it)
    op.execute('DROP EXTENSION IF EXISTS vector CASCADE')
