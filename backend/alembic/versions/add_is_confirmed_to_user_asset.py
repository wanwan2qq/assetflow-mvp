"""add is_confirmed field to user_asset

Revision ID: add_is_confirmed_field
Revises: phase4_add_vector_memory_table
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_confirmed_field'
down_revision = 'phase4_vector_memory'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_confirmed field to user_asset table"""
    # Check if column already exists (for idempotency)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('userasset')]
    
    if 'is_confirmed' not in columns:
        op.add_column('userasset', sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default='false'))
        print("✅ Added is_confirmed column to userasset table")
    else:
        print("ℹ️  is_confirmed column already exists in userasset table")


def downgrade() -> None:
    """Remove is_confirmed field from user_asset table"""
    op.drop_column('userasset', 'is_confirmed')
