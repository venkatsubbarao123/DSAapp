"""create_phase7_practice_gamification_tables

Revision ID: 5a918b2c4e3f
Revises: 48d617fa918b
Create Date: 2026-09-29 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a918b2c4e3f'
down_revision: Union[str, Sequence[str], None] = '48d617fa918b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include Phase 7 practice and gamification tables."""
    # 1. practice_sessions
    op.create_table(
        'practice_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('mode', sa.String(length=32), nullable=False, server_default='QUICK'),
        sa.Column('topic_id', sa.String(length=36), nullable=True),
        sa.Column('pattern_id', sa.String(length=36), nullable=True),
        sa.Column('difficulty', sa.String(length=32), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('target_count', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('completed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('solved_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('xp_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accuracy', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_practice_sessions_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_practice_sessions_topic_id_topics'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pattern_id'], ['patterns.id'], name=op.f('fk_practice_sessions_pattern_id_patterns'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_practice_sessions')),
    )
    op.create_index(op.f('ix_practice_sessions_user_id'), 'practice_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_practice_sessions_mode'), 'practice_sessions', ['mode'], unique=False)
    op.create_index(op.f('ix_practice_sessions_status'), 'practice_sessions', ['status'], unique=False)
    op.create_index('ix_practice_sessions_user_status', 'practice_sessions', ['user_id', 'status'], unique=False)
    op.create_index('ix_practice_sessions_user_created', 'practice_sessions', ['user_id', 'created_at'], unique=False)

    # 2. practice_session_problems
    op.create_table(
        'practice_session_problems',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('problem_id', sa.String(length=36), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('served_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('solved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('submission_id', sa.String(length=36), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['practice_sessions.id'], name=op.f('fk_practice_session_problems_session_id'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], name=op.f('fk_practice_session_problems_problem_id'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], name=op.f('fk_practice_session_problems_submission_id'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_practice_session_problems')),
        sa.UniqueConstraint('session_id', 'problem_id', name='uq_practice_session_problem'),
    )
    op.create_index(op.f('ix_practice_session_problems_session_id'), 'practice_session_problems', ['session_id'], unique=False)
    op.create_index(op.f('ix_practice_session_problems_problem_id'), 'practice_session_problems', ['problem_id'], unique=False)
    op.create_index('ix_session_problem_session_seq', 'practice_session_problems', ['session_id', 'sequence'], unique=False)

    # 3. xp_transactions
    op.create_table(
        'xp_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('source_id', sa.String(length=128), nullable=False),
        sa.Column('idempotency_key', sa.String(length=160), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_xp_transactions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_xp_transactions')),
        sa.UniqueConstraint('idempotency_key', name=op.f('uq_xp_transactions_idempotency_key')),
    )
    op.create_index(op.f('ix_xp_transactions_user_id'), 'xp_transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_xp_transactions_event_type'), 'xp_transactions', ['event_type'], unique=False)
    op.create_index(op.f('ix_xp_transactions_created_at'), 'xp_transactions', ['created_at'], unique=False)
    op.create_index('ix_xp_trans_user_created', 'xp_transactions', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_xp_trans_user_event', 'xp_transactions', ['user_id', 'event_type'], unique=False)

    # 4. user_gamification_profiles
    op.create_table(
        'user_gamification_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('total_xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_activity_date', sa.String(length=10), nullable=True),
        sa.Column('streak_freeze_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_rating', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('total_solves', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_gamification_profiles_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_gamification_profiles')),
        sa.UniqueConstraint('user_id', name=op.f('uq_user_gamification_profiles_user_id')),
    )
    op.create_index(op.f('ix_user_gamification_profiles_user_id'), 'user_gamification_profiles', ['user_id'], unique=True)
    op.create_index(op.f('ix_user_gamification_profiles_total_xp'), 'user_gamification_profiles', ['total_xp'], unique=False)
    op.create_index(op.f('ix_user_gamification_profiles_current_level'), 'user_gamification_profiles', ['current_level'], unique=False)
    op.create_index(op.f('ix_user_gamification_profiles_current_streak'), 'user_gamification_profiles', ['current_streak'], unique=False)
    op.create_index(op.f('ix_user_gamification_profiles_current_rating'), 'user_gamification_profiles', ['current_rating'], unique=False)
    op.create_index(op.f('ix_user_gamification_profiles_total_solves'), 'user_gamification_profiles', ['total_solves'], unique=False)
    op.create_index('ix_gamification_xp_rank', 'user_gamification_profiles', ['total_xp'], unique=False)
    op.create_index('ix_gamification_solves_rank', 'user_gamification_profiles', ['total_solves'], unique=False)
    op.create_index('ix_gamification_streak_rank', 'user_gamification_profiles', ['current_streak'], unique=False)

    # 5. daily_challenges
    op.create_table(
        'daily_challenges',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('challenge_date', sa.String(length=10), nullable=False),
        sa.Column('problem_id', sa.String(length=36), nullable=False),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('bonus_xp', sa.Integer(), nullable=False, server_default='25'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], name=op.f('fk_daily_challenges_problem_id_problems'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_daily_challenges')),
        sa.UniqueConstraint('challenge_date', name=op.f('uq_daily_challenges_challenge_date')),
    )
    op.create_index(op.f('ix_daily_challenges_challenge_date'), 'daily_challenges', ['challenge_date'], unique=True)
    op.create_index(op.f('ix_daily_challenges_problem_id'), 'daily_challenges', ['problem_id'], unique=False)

    # 6. user_daily_challenges
    op.create_table(
        'user_daily_challenges',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('daily_challenge_id', sa.String(length=36), nullable=False),
        sa.Column('challenge_date', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ATTEMPTED'),
        sa.Column('attempts_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('solved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('first_attempt_solve', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('xp_awarded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_daily_challenges_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['daily_challenge_id'], ['daily_challenges.id'], name=op.f('fk_user_daily_challenges_daily_challenge_id'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_daily_challenges')),
        sa.UniqueConstraint('user_id', 'challenge_date', name='uq_user_daily_challenge_date'),
    )
    op.create_index(op.f('ix_user_daily_challenges_user_id'), 'user_daily_challenges', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_daily_challenges_daily_challenge_id'), 'user_daily_challenges', ['daily_challenge_id'], unique=False)
    op.create_index(op.f('ix_user_daily_challenges_challenge_date'), 'user_daily_challenges', ['challenge_date'], unique=False)
    op.create_index('ix_user_daily_challenges_user_solved', 'user_daily_challenges', ['user_id', 'solved'], unique=False)

    # 7. achievements
    op.create_table(
        'achievements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('tier', sa.String(length=16), nullable=False, server_default='BRONZE'),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('icon', sa.String(length=64), nullable=False, server_default='trophy'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_achievements')),
        sa.UniqueConstraint('code', name=op.f('uq_achievements_code')),
    )
    op.create_index(op.f('ix_achievements_code'), 'achievements', ['code'], unique=True)
    op.create_index(op.f('ix_achievements_category'), 'achievements', ['category'], unique=False)

    # 8. user_achievements
    op.create_table(
        'user_achievements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('achievement_id', sa.String(length=36), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notified', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_achievements_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], name=op.f('fk_user_achievements_achievement_id_achievements'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_achievements')),
        sa.UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement'),
    )
    op.create_index(op.f('ix_user_achievements_user_id'), 'user_achievements', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_achievements_achievement_id'), 'user_achievements', ['achievement_id'], unique=False)
    op.create_index('ix_user_achievements_user_unlocked', 'user_achievements', ['user_id', 'unlocked_at'], unique=False)

    # 9. rating_history
    op.create_table(
        'rating_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('previous_rating', sa.Integer(), nullable=False),
        sa.Column('new_rating', sa.Integer(), nullable=False),
        sa.Column('change', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=128), nullable=False),
        sa.Column('source_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_rating_history_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_rating_history')),
    )
    op.create_index(op.f('ix_rating_history_user_id'), 'rating_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_rating_history_created_at'), 'rating_history', ['created_at'], unique=False)
    op.create_index('ix_rating_history_user_created', 'rating_history', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema removing Phase 7 tables."""
    op.drop_table('rating_history')
    op.drop_table('user_achievements')
    op.drop_table('achievements')
    op.drop_table('user_daily_challenges')
    op.drop_table('daily_challenges')
    op.drop_table('user_gamification_profiles')
    op.drop_table('xp_transactions')
    op.drop_table('practice_session_problems')
    op.drop_table('practice_sessions')
