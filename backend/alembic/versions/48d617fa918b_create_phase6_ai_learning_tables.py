"""create_phase6_ai_learning_tables

Revision ID: 48d617fa918b
Revises: 3539af27d2f1
Create Date: 2026-09-29 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48d617fa918b'
down_revision: Union[str, Sequence[str], None] = '3539af27d2f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include Phase 6 AI learning tables."""
    # 1. ai_usage table
    op.create_table(
        'ai_usage',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('request_type', sa.String(length=32), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('model', sa.String(length=64), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_ai_usage_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_usage')),
    )
    op.create_index(op.f('ix_ai_usage_user_id'), 'ai_usage', ['user_id'], unique=False)
    op.create_index(op.f('ix_ai_usage_request_type'), 'ai_usage', ['request_type'], unique=False)
    op.create_index(op.f('ix_ai_usage_created_at'), 'ai_usage', ['created_at'], unique=False)
    op.create_index('ix_ai_usage_user_created', 'ai_usage', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_ai_usage_user_type_created', 'ai_usage', ['user_id', 'request_type', 'created_at'], unique=False)

    # 2. ai_conversations table
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('problem_id', sa.String(length=36), nullable=True),
        sa.Column('lesson_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_ai_conversations_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], name=op.f('fk_ai_conversations_problem_id_problems'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name=op.f('fk_ai_conversations_lesson_id_lessons'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_conversations')),
    )
    op.create_index(op.f('ix_ai_conversations_user_id'), 'ai_conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_ai_conversations_problem_id'), 'ai_conversations', ['problem_id'], unique=False)
    op.create_index(op.f('ix_ai_conversations_lesson_id'), 'ai_conversations', ['lesson_id'], unique=False)
    op.create_index('ix_ai_conversations_user_updated', 'ai_conversations', ['user_id', 'updated_at'], unique=False)

    # 3. ai_messages table
    op.create_table(
        'ai_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=16), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], name=op.f('fk_ai_messages_conversation_id_ai_conversations'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_messages')),
    )
    op.create_index(op.f('ix_ai_messages_conversation_id'), 'ai_messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_ai_messages_created_at'), 'ai_messages', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_ai_messages_created_at'), table_name='ai_messages')
    op.drop_index(op.f('ix_ai_messages_conversation_id'), table_name='ai_messages')
    op.drop_table('ai_messages')

    op.drop_index('ix_ai_conversations_user_updated', table_name='ai_conversations')
    op.drop_index(op.f('ix_ai_conversations_lesson_id'), table_name='ai_conversations')
    op.drop_index(op.f('ix_ai_conversations_problem_id'), table_name='ai_conversations')
    op.drop_index(op.f('ix_ai_conversations_user_id'), table_name='ai_conversations')
    op.drop_table('ai_conversations')

    op.drop_index('ix_ai_usage_user_type_created', table_name='ai_usage')
    op.drop_index('ix_ai_usage_user_created', table_name='ai_usage')
    op.drop_index(op.f('ix_ai_usage_created_at'), table_name='ai_usage')
    op.drop_index(op.f('ix_ai_usage_request_type'), table_name='ai_usage')
    op.drop_index(op.f('ix_ai_usage_user_id'), table_name='ai_usage')
    op.drop_table('ai_usage')
