"""Add GIN indexes for JSONB fields

Revision ID: add_gin_indexes
Revises: fadbbb43c01c
Create Date: 2026-01-23

This migration adds GIN indexes to optimize JSONB field queries:
- UserAsset.extra_data
- RealEstateAsset.extra_data
- PolicyKnowledge.keywords
- FAQKnowledge.keywords
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'add_gin_indexes'
down_revision = None  # Will be set automatically by alembic
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First convert JSON columns to JSONB (required for GIN with jsonb_path_ops)
    op.execute("ALTER TABLE userasset ALTER COLUMN extra_data TYPE jsonb USING extra_data::jsonb")
    op.execute("ALTER TABLE real_estate_asset ALTER COLUMN extra_data TYPE jsonb USING extra_data::jsonb")
    op.execute("ALTER TABLE policy_knowledge ALTER COLUMN keywords TYPE jsonb USING keywords::jsonb")
    op.execute("ALTER TABLE faq_knowledge ALTER COLUMN keywords TYPE jsonb USING keywords::jsonb")
    
    # Add GIN index on UserAsset.extra_data for faster JSONB queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_userasset_extra_data_gin 
        ON userasset USING GIN (extra_data jsonb_path_ops)
    """)
    
    # Add GIN index on RealEstateAsset.extra_data
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_real_estate_asset_extra_data_gin 
        ON real_estate_asset USING GIN (extra_data jsonb_path_ops)
    """)
    
    # Add GIN index on PolicyKnowledge.keywords for faster keyword containment queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_policy_knowledge_keywords_gin 
        ON policy_knowledge USING GIN (keywords jsonb_path_ops)
    """)
    
    # Add GIN index on FAQKnowledge.keywords
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_faq_knowledge_keywords_gin 
        ON faq_knowledge USING GIN (keywords jsonb_path_ops)
    """)
    
    print("✅ GIN indexes created successfully")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_userasset_extra_data_gin")
    op.execute("DROP INDEX IF EXISTS ix_real_estate_asset_extra_data_gin")
    op.execute("DROP INDEX IF EXISTS ix_policy_knowledge_keywords_gin")
    op.execute("DROP INDEX IF EXISTS ix_faq_knowledge_keywords_gin")
    
    # Revert JSONB back to JSON
    op.execute("ALTER TABLE userasset ALTER COLUMN extra_data TYPE json USING extra_data::json")
    op.execute("ALTER TABLE real_estate_asset ALTER COLUMN extra_data TYPE json USING extra_data::json")
    op.execute("ALTER TABLE policy_knowledge ALTER COLUMN keywords TYPE json USING keywords::json")
    op.execute("ALTER TABLE faq_knowledge ALTER COLUMN keywords TYPE json USING keywords::json")
