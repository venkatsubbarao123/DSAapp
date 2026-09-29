"""create_phase8_contest_interview_cp_sql_tables

Revision ID: 6b029c3d5e7f
Revises: 5a918b2c4e3f
Create Date: 2026-09-29 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b029c3d5e7f'
down_revision: Union[str, Sequence[str], None] = '5a918b2c4e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include Phase 8 Contests, Interview, CP, and SQL tables."""
    # 1. contests
    op.create_table(
        'contests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DRAFT'),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='7200'),
        sa.Column('visibility', sa.String(length=32), nullable=False, server_default='PUBLIC'),
        sa.Column('premium_required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contests')),
    )
    op.create_index(op.f('ix_contests_slug'), 'contests', ['slug'], unique=True)
    op.create_index(op.f('ix_contests_status'), 'contests', ['status'], unique=False)
    op.create_index(op.f('ix_contests_start_at'), 'contests', ['start_at'], unique=False)
    op.create_index(op.f('ix_contests_end_at'), 'contests', ['end_at'], unique=False)

    # 2. contest_problems
    op.create_table(
        'contest_problems',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('contest_id', sa.String(length=36), nullable=False),
        sa.Column('problem_id', sa.String(length=36), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('points', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('penalty_minutes', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('difficulty', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.ForeignKeyConstraint(['contest_id'], ['contests.id'], name=op.f('fk_contest_problems_contest_id_contests'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], name=op.f('fk_contest_problems_problem_id_problems'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contest_problems')),
        sa.UniqueConstraint('contest_id', 'problem_id', name='uq_contest_problem'),
        sa.UniqueConstraint('contest_id', 'sequence', name='uq_contest_sequence'),
    )
    op.create_index(op.f('ix_contest_problems_contest_id'), 'contest_problems', ['contest_id'], unique=False)
    op.create_index(op.f('ix_contest_problems_problem_id'), 'contest_problems', ['problem_id'], unique=False)
    op.create_index('ix_contest_problems_contest_seq', 'contest_problems', ['contest_id', 'sequence'], unique=False)

    # 3. contest_participants
    op.create_table(
        'contest_participants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('contest_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('final_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('final_penalty', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('final_rank', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['contest_id'], ['contests.id'], name=op.f('fk_contest_participants_contest_id_contests'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_contest_participants_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contest_participants')),
        sa.UniqueConstraint('contest_id', 'user_id', name='uq_contest_user'),
    )
    op.create_index(op.f('ix_contest_participants_contest_id'), 'contest_participants', ['contest_id'], unique=False)
    op.create_index(op.f('ix_contest_participants_user_id'), 'contest_participants', ['user_id'], unique=False)
    op.create_index('ix_contest_participants_score', 'contest_participants', ['contest_id', 'final_score', 'final_penalty'], unique=False)

    # 4. contest_submissions
    op.create_table(
        'contest_submissions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('contest_id', sa.String(length=36), nullable=False),
        sa.Column('participant_id', sa.String(length=36), nullable=False),
        sa.Column('problem_id', sa.String(length=36), nullable=False),
        sa.Column('submission_id', sa.String(length=36), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verdict', sa.String(length=64), nullable=False, server_default='QUEUED'),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('penalty', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['contest_id'], ['contests.id'], name=op.f('fk_contest_submissions_contest_id_contests'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['participant_id'], ['contest_participants.id'], name=op.f('fk_contest_submissions_participant_id'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], name=op.f('fk_contest_submissions_problem_id_problems'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], name=op.f('fk_contest_submissions_submission_id_submissions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contest_submissions')),
        sa.UniqueConstraint('submission_id', name=op.f('uq_contest_submissions_submission_id')),
    )
    op.create_index(op.f('ix_contest_submissions_contest_id'), 'contest_submissions', ['contest_id'], unique=False)
    op.create_index(op.f('ix_contest_submissions_participant_id'), 'contest_submissions', ['participant_id'], unique=False)
    op.create_index(op.f('ix_contest_submissions_problem_id'), 'contest_submissions', ['problem_id'], unique=False)
    op.create_index(op.f('ix_contest_submissions_submitted_at'), 'contest_submissions', ['submitted_at'], unique=False)
    op.create_index('ix_contest_submissions_contest_prob', 'contest_submissions', ['contest_id', 'problem_id'], unique=False)

    # 5. contest_cheat_signals
    op.create_table(
        'contest_cheat_signals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('contest_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('signal_type', sa.String(length=64), nullable=False),
        sa.Column('details_json', sa.JSON(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['contest_id'], ['contests.id'], name=op.f('fk_contest_cheat_signals_contest_id_contests'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_contest_cheat_signals_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contest_cheat_signals')),
    )
    op.create_index(op.f('ix_contest_cheat_signals_contest_id'), 'contest_cheat_signals', ['contest_id'], unique=False)
    op.create_index(op.f('ix_contest_cheat_signals_user_id'), 'contest_cheat_signals', ['user_id'], unique=False)
    op.create_index(op.f('ix_contest_cheat_signals_detected_at'), 'contest_cheat_signals', ['detected_at'], unique=False)

    # 6. interview_sessions
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('mode', sa.String(length=32), nullable=False, server_default='GENERAL_SOFTWARE'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='2700'),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('answered_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('evaluation_status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('feedback_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_interview_sessions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_sessions')),
    )
    op.create_index(op.f('ix_interview_sessions_user_id'), 'interview_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_interview_sessions_mode'), 'interview_sessions', ['mode'], unique=False)
    op.create_index(op.f('ix_interview_sessions_status'), 'interview_sessions', ['status'], unique=False)
    op.create_index('ix_interview_sessions_user_status', 'interview_sessions', ['user_id', 'status'], unique=False)

    # 7. interview_questions
    op.create_table(
        'interview_questions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.String(length=32), nullable=False),
        sa.Column('question_title', sa.String(length=255), nullable=False),
        sa.Column('question_prompt', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_option', sa.String(length=255), nullable=True),
        sa.Column('difficulty', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_answer', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('evaluation_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], name=op.f('fk_interview_questions_session_id_sessions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_questions')),
    )
    op.create_index(op.f('ix_interview_questions_session_id'), 'interview_questions', ['session_id'], unique=False)
    op.create_index('ix_interview_questions_session_seq', 'interview_questions', ['session_id', 'sequence'], unique=False)

    # 8. cp_problem_metadata
    op.create_table(
        'cp_problem_metadata',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('problem_id', sa.String(length=36), nullable=False),
        sa.Column('rating_band', sa.Integer(), nullable=False, server_default='1200'),
        sa.Column('time_limit_ms', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('memory_limit_mb', sa.Integer(), nullable=False, server_default='256'),
        sa.Column('input_format', sa.Text(), nullable=False, server_default=''),
        sa.Column('output_format', sa.Text(), nullable=False, server_default=''),
        sa.Column('constraints', sa.Text(), nullable=False, server_default=''),
        sa.Column('editorial', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], name=op.f('fk_cp_problem_metadata_problem_id_problems'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cp_problem_metadata')),
        sa.UniqueConstraint('problem_id', name=op.f('uq_cp_problem_metadata_problem_id')),
    )
    op.create_index(op.f('ix_cp_problem_metadata_problem_id'), 'cp_problem_metadata', ['problem_id'], unique=True)
    op.create_index(op.f('ix_cp_problem_metadata_rating_band'), 'cp_problem_metadata', ['rating_band'], unique=False)

    # 9. competitive_ratings
    op.create_table(
        'competitive_ratings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('current_rating', sa.Integer(), nullable=False, server_default='1200'),
        sa.Column('peak_rating', sa.Integer(), nullable=False, server_default='1200'),
        sa.Column('contests_played', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('contests_won', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('problems_solved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_competitive_ratings_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_competitive_ratings')),
        sa.UniqueConstraint('user_id', name=op.f('uq_competitive_ratings_user_id')),
    )
    op.create_index(op.f('ix_competitive_ratings_user_id'), 'competitive_ratings', ['user_id'], unique=True)
    op.create_index(op.f('ix_competitive_ratings_current_rating'), 'competitive_ratings', ['current_rating'], unique=False)

    # 10. competitive_rating_history
    op.create_table(
        'competitive_rating_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('previous_rating', sa.Integer(), nullable=False),
        sa.Column('new_rating', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=64), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_competitive_rating_history_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_competitive_rating_history')),
    )
    op.create_index(op.f('ix_competitive_rating_history_user_id'), 'competitive_rating_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_competitive_rating_history_created_at'), 'competitive_rating_history', ['created_at'], unique=False)
    op.create_index('ix_cp_rating_hist_user_created', 'competitive_rating_history', ['user_id', 'created_at'], unique=False)

    # 11. sql_problems
    op.create_table(
        'sql_problems',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('difficulty', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('category', sa.String(length=64), nullable=False, server_default='BASICS'),
        sa.Column('schema_ddl', sa.Text(), nullable=False),
        sa.Column('seed_data_sql', sa.Text(), nullable=False),
        sa.Column('solution_sql', sa.Text(), nullable=False),
        sa.Column('is_order_sensitive', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('allowed_features', sa.String(length=255), nullable=True),
        sa.Column('time_limit_seconds', sa.Float(), nullable=False, server_default='3.0'),
        sa.Column('access_level', sa.String(length=32), nullable=False, server_default='FREE'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sql_problems')),
    )
    op.create_index(op.f('ix_sql_problems_slug'), 'sql_problems', ['slug'], unique=True)
    op.create_index(op.f('ix_sql_problems_category'), 'sql_problems', ['category'], unique=False)
    op.create_index(op.f('ix_sql_problems_is_published'), 'sql_problems', ['is_published'], unique=False)

    # 12. sql_submissions
    op.create_table(
        'sql_submissions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('sql_problem_id', sa.String(length=36), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('verdict', sa.String(length=64), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_sql_submissions_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sql_problem_id'], ['sql_problems.id'], name=op.f('fk_sql_submissions_sql_problem_id'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sql_submissions')),
    )
    op.create_index(op.f('ix_sql_submissions_user_id'), 'sql_submissions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sql_submissions_sql_problem_id'), 'sql_submissions', ['sql_problem_id'], unique=False)
    op.create_index(op.f('ix_sql_submissions_created_at'), 'sql_submissions', ['created_at'], unique=False)
    op.create_index('ix_sql_submissions_user_problem', 'sql_submissions', ['user_id', 'sql_problem_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema by dropping Phase 8 tables in reverse order."""
    op.drop_table('sql_submissions')
    op.drop_table('sql_problems')
    op.drop_table('competitive_rating_history')
    op.drop_table('competitive_ratings')
    op.drop_table('cp_problem_metadata')
    op.drop_table('interview_questions')
    op.drop_table('interview_sessions')
    op.drop_table('contest_cheat_signals')
    op.drop_table('contest_submissions')
    op.drop_table('contest_participants')
    op.drop_table('contest_problems')
    op.drop_table('contests')
