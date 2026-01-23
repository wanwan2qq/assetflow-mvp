"""add_real_estate_asset_table

Revision ID: 31ee11693efe
Revises: 2e0176ff710f
Create Date: 2026-01-20 10:28:22.330458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '31ee11693efe'
down_revision: Union[str, None] = '2e0176ff710f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create real_estate_asset table for Phase 2"""
    op.create_table(
        'real_estate_asset',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # 基础信息
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('property_type', sa.String(length=20), nullable=False, server_default='residential'),
        sa.Column('usage', sa.String(length=20), nullable=False, server_default='self_occupied'),
        
        # 位置信息
        sa.Column('city', sa.String(length=50), nullable=False),
        sa.Column('district', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        
        # 物理属性
        sa.Column('area', sa.Float(), nullable=False),
        sa.Column('bedrooms', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('year_built', sa.Integer(), nullable=True),
        
        # 价值信息
        sa.Column('purchase_price', sa.Float(), nullable=True),
        sa.Column('purchase_date', sa.DateTime(), nullable=True),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('value_source', sa.String(length=50), nullable=False, server_default='user_input'),
        sa.Column('value_confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('value_updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        
        # 贷款信息
        sa.Column('loan_type', sa.String(length=20), nullable=False, server_default='none'),
        sa.Column('loan_balance', sa.Float(), nullable=False, server_default='0'),
        sa.Column('monthly_payment', sa.Float(), nullable=False, server_default='0'),
        sa.Column('loan_rate', sa.Float(), nullable=True),
        sa.Column('loan_remaining_months', sa.Integer(), nullable=True),
        
        # 租赁信息
        sa.Column('monthly_rent', sa.Float(), nullable=True),
        sa.Column('rental_yield', sa.Float(), nullable=True),
        
        # 金融属性 (计算字段)
        sa.Column('mortgage_potential', sa.Float(), nullable=True),
        sa.Column('net_equity', sa.Float(), nullable=True),
        
        # 扩展数据
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        
        # 关联原 UserAsset
        sa.Column('legacy_asset_id', sa.Integer(), nullable=True),
        
        # 主键和外键
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_real_estate_asset_user_id'),
    )
    
    # 创建索引
    op.create_index('ix_real_estate_asset_user_id', 'real_estate_asset', ['user_id'])
    op.create_index('ix_real_estate_asset_city', 'real_estate_asset', ['city'])


def downgrade() -> None:
    """Drop real_estate_asset table"""
    op.drop_index('ix_real_estate_asset_city', table_name='real_estate_asset')
    op.drop_index('ix_real_estate_asset_user_id', table_name='real_estate_asset')
    op.drop_table('real_estate_asset')