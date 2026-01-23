"""add_phase4_action_plan_and_family_profile_tables

Revision ID: fadbbb43c01c
Revises: 264b7923a636
Create Date: 2026-01-20 16:15:47.845552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fadbbb43c01c'
down_revision: Union[str, None] = '264b7923a636'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 4 tables: action_plan and family_profile"""
    # Create action_plan table
    op.create_table('action_plan',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('expected_benefits', sa.JSON(), nullable=True),
        sa.Column('potential_risks', sa.JSON(), nullable=True),
        sa.Column('based_on_assets', sa.JSON(), nullable=True),
        sa.Column('based_on_knowledge', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('completed_steps', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_action_plan_user_id'), 'action_plan', ['user_id'], unique=False)
    
    # Create family_profile table
    op.create_table('family_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('members', sa.JSON(), nullable=True),
        sa.Column('lifecycle_events', sa.JSON(), nullable=True),
        sa.Column('total_income', sa.Float(), nullable=True),
        sa.Column('total_expenses', sa.Float(), nullable=True),
        sa.Column('financial_goals', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_profile_user_id'), 'family_profile', ['user_id'], unique=True)


def downgrade() -> None:
    """Remove Phase 4 tables"""
    op.drop_index(op.f('ix_family_profile_user_id'), table_name='family_profile')
    op.drop_table('family_profile')
    op.drop_index(op.f('ix_action_plan_user_id'), table_name='action_plan')
    op.drop_table('action_plan')