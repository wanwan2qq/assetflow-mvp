"""add_chat_message_table_manual

Revision ID: add_chat_message_table_manual
Revises: d597c13bb774
Create Date: 2026-01-13 17:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "add_chat_message_table_manual"
down_revision: Union[str, None] = "d597c13bb774"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the ChatMessage table (enum already exists)
    op.create_table(
        'chatmessage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('USER', 'AI', name='messagerole', create_type=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_chatmessage_user_id'), 'chatmessage', ['user_id'], unique=False)
    op.create_index(op.f('ix_chatmessage_role'), 'chatmessage', ['role'], unique=False)
    op.create_index(op.f('ix_chatmessage_timestamp'), 'chatmessage', ['timestamp'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_chatmessage_timestamp'), table_name='chatmessage')
    op.drop_index(op.f('ix_chatmessage_role'), table_name='chatmessage')
    op.drop_index(op.f('ix_chatmessage_user_id'), table_name='chatmessage')
    
    # Drop table
    op.drop_table('chatmessage')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS messagerole')