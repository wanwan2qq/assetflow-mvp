"""add knowledge tables for RAG

Revision ID: 264b7923a636
Revises: 31ee11693efe
Create Date: 2026-01-20 13:03:38.594081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '264b7923a636'
down_revision: Union[str, None] = '31ee11693efe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create knowledge tables for RAG system."""
    
    # PolicyKnowledge table
    op.create_table(
        'policy_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('city', sa.String(length=50), nullable=True),
        sa.Column('region', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('conditions', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(length=200), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('effective_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_policy_knowledge_city', 'policy_knowledge', ['city'])
    op.create_index('ix_policy_knowledge_category', 'policy_knowledge', ['category'])
    op.create_index('ix_policy_knowledge_status', 'policy_knowledge', ['status'])

    # FAQKnowledge table
    op.create_table(
        'faq_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.String(length=500), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('helpful_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_faq_knowledge_category', 'faq_knowledge', ['category'])
    op.create_index('ix_faq_knowledge_status', 'faq_knowledge', ['status'])

    # ProductKnowledge table
    op.create_table(
        'product_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('product_type', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('suitable_for', sa.JSON(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_product_knowledge_type', 'product_knowledge', ['product_type'])
    op.create_index('ix_product_knowledge_status', 'product_knowledge', ['status'])


def downgrade() -> None:
    """Drop knowledge tables."""
    op.drop_index('ix_product_knowledge_status', table_name='product_knowledge')
    op.drop_index('ix_product_knowledge_type', table_name='product_knowledge')
    op.drop_table('product_knowledge')
    
    op.drop_index('ix_faq_knowledge_status', table_name='faq_knowledge')
    op.drop_index('ix_faq_knowledge_category', table_name='faq_knowledge')
    op.drop_table('faq_knowledge')
    
    op.drop_index('ix_policy_knowledge_status', table_name='policy_knowledge')
    op.drop_index('ix_policy_knowledge_category', table_name='policy_knowledge')
    op.drop_index('ix_policy_knowledge_city', table_name='policy_knowledge')
    op.drop_table('policy_knowledge')