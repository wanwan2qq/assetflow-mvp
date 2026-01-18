"""add memory extraction tracking

Revision ID: add_memory_tracking
Revises: cc1330024231
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_memory_tracking'
down_revision = 'cc1330024231'
branch_labels = None
depends_on = None


def upgrade():
    # Add tracking fields to user_cognition table
    op.add_column('user_cognition', 
        sa.Column('last_analyzed_message_id', sa.Integer(), nullable=True)
    )
    op.add_column('user_cognition',
        sa.Column('last_memory_extraction_at', sa.DateTime(), nullable=True)
    )
    
    # Add index for performance
    op.create_index(
        'idx_user_cognition_last_analyzed',
        'user_cognition',
        ['user_id', 'last_analyzed_message_id']
    )


def downgrade():
    # Remove index
    op.drop_index('idx_user_cognition_last_analyzed', table_name='user_cognition')
    
    # Remove columns
    op.drop_column('user_cognition', 'last_memory_extraction_at')
    op.drop_column('user_cognition', 'last_analyzed_message_id')
