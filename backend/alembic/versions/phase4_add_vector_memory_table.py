"""Phase 4: Add vector_memory table for L3 long-term memory

Revision ID: phase4_vector_memory
Revises: phase4_pgvector
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'phase4_vector_memory'
down_revision = 'phase4_pgvector'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vector_memory table with 1024-dimensional vectors for BGE embeddings"""
    op.create_table(
        'vector_memory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        # CRITICAL: BGE-Large uses 1024 dimensions
        sa.Column('embedding', Vector(1024), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_vector_memory_user_id', 'vector_memory', ['user_id'], unique=False)
    op.create_index('ix_vector_memory_user_created', 'vector_memory', ['user_id', 'created_at'], unique=False)
    
    # Create vector similarity index using pgvector (HNSW for fast approximate search)
    # This requires pgvector extension to be enabled
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vector_memory_embedding_cosine 
        ON vector_memory 
        USING hnsw (embedding vector_cosine_ops)
    """)


def downgrade() -> None:
    """Drop vector_memory table"""
    op.drop_index('ix_vector_memory_embedding_cosine', table_name='vector_memory')
    op.drop_index('ix_vector_memory_user_created', table_name='vector_memory')
    op.drop_index('ix_vector_memory_user_id', table_name='vector_memory')
    op.drop_table('vector_memory')
