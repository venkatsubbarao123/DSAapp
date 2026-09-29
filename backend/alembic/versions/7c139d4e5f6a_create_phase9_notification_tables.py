"""create_phase9_notification_tables

Revision ID: 7c139d4e5f6a
Revises: 6b029c3d5e7f
Create Date: 2026-09-29 23:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c139d4e5f6a'
down_revision: Union[str, Sequence[str], None] = '6b029c3d5e7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include Phase 9 Notification, Preferences, and Delivery tables."""
    # 1. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)
    op.create_index(op.f('ix_notifications_read_at'), 'notifications', ['read_at'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'read_at'], unique=False)
    op.create_index('idx_notifications_user_created', 'notifications', ['user_id', 'created_at'], unique=False)

    # 2. notification_preferences
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('daily_challenge', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('streak_reminders', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('revision_reminders', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('contest_notifications', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('achievement_notifications', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('system_notifications', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_notification_preferences_user_id')
    )
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=True)

    # 3. notification_deliveries
    op.create_table(
        'notification_deliveries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('notification_id', sa.String(length=36), nullable=False),
        sa.Column('channel', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='QUEUED'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('provider_message_id', sa.String(length=128), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_deliveries_id'), 'notification_deliveries', ['id'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_notification_id'), 'notification_deliveries', ['notification_id'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_channel'), 'notification_deliveries', ['channel'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_status'), 'notification_deliveries', ['status'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_created_at'), 'notification_deliveries', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema dropping notification tables in reverse topological order."""
    op.drop_table('notification_deliveries')
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
