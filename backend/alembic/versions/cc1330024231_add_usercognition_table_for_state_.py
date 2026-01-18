"""Add UserCognition table for state management

Revision ID: cc1330024231
Revises: add_chat_message_table_manual
Create Date: 2026-01-13 18:00:59.789339

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cc1330024231"
down_revision: Union[str, None] = "add_chat_message_table_manual"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_cognition table
    op.create_table(
        'user_cognition',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('financial_goals', sa.JSON(), nullable=True),
        sa.Column('risk_profile', sa.JSON(), nullable=True),
        sa.Column('collection_status', sa.JSON(), nullable=True),
        sa.Column('advisor_note', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_cognition_user_id'), 'user_cognition', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_cognition_user_id'), table_name='user_cognition')
    op.drop_table('user_cognition')
