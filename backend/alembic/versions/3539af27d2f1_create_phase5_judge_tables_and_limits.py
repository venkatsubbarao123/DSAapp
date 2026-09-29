"""create_phase5_judge_tables_and_limits

Revision ID: 3539af27d2f1
Revises: 30cb1c9a63d3
Create Date: 2026-09-29 16:19:36.193922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3539af27d2f1'
down_revision: Union[str, Sequence[str], None] = '30cb1c9a63d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('judge_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('submission_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.Enum('QUEUED', 'CLAIMED', 'RUNNING', 'COMPLETED', 'FAILED', 'RETRY_PENDING', 'CANCELLED', name='judgejobstatus'), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.String(length=64), nullable=True),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], name=op.f('fk_judge_jobs_submission_id_submissions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_judge_jobs'))
    )
    op.create_index('ix_judge_jobs_heartbeat', 'judge_jobs', ['status', 'heartbeat_at'], unique=False)
    op.create_index(op.f('ix_judge_jobs_heartbeat_at'), 'judge_jobs', ['heartbeat_at'], unique=False)
    op.create_index(op.f('ix_judge_jobs_status'), 'judge_jobs', ['status'], unique=False)
    op.create_index('ix_judge_jobs_status_queued_at', 'judge_jobs', ['status', 'queued_at'], unique=False)
    op.create_index(op.f('ix_judge_jobs_submission_id'), 'judge_jobs', ['submission_id'], unique=True)
    op.create_index(op.f('ix_judge_jobs_worker_id'), 'judge_jobs', ['worker_id'], unique=False)

    op.create_table('submission_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('submission_id', sa.String(length=36), nullable=False),
        sa.Column('verdict', sa.Enum('ACCEPTED', 'WRONG_ANSWER', 'TIME_LIMIT_EXCEEDED', 'MEMORY_LIMIT_EXCEEDED', 'RUNTIME_ERROR', 'COMPILATION_ERROR', 'OUTPUT_LIMIT_EXCEEDED', 'SYSTEM_ERROR', name='verdict'), nullable=False),
        sa.Column('tests_total', sa.Integer(), nullable=False),
        sa.Column('tests_passed', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('memory_used_bytes', sa.Integer(), nullable=True),
        sa.Column('compiler_output_safe', sa.Text(), nullable=True),
        sa.Column('runtime_output_safe', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], name=op.f('fk_submission_results_submission_id_submissions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_submission_results'))
    )
    op.create_index(op.f('ix_submission_results_submission_id'), 'submission_results', ['submission_id'], unique=True)
    op.create_index(op.f('ix_submission_results_verdict'), 'submission_results', ['verdict'], unique=False)

    with op.batch_alter_table('problems') as batch_op:
        batch_op.add_column(sa.Column('time_limit_ms', sa.Integer(), nullable=False, server_default='2000'))
        batch_op.add_column(sa.Column('memory_limit_mb', sa.Integer(), nullable=False, server_default='256'))
        batch_op.add_column(sa.Column('output_limit_bytes', sa.Integer(), nullable=False, server_default='65536'))
        batch_op.add_column(sa.Column('comparison_mode', sa.String(length=32), nullable=False, server_default='exact'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('problems') as batch_op:
        batch_op.drop_column('comparison_mode')
        batch_op.drop_column('output_limit_bytes')
        batch_op.drop_column('memory_limit_mb')
        batch_op.drop_column('time_limit_ms')

    op.drop_index(op.f('ix_submission_results_verdict'), table_name='submission_results')
    op.drop_index(op.f('ix_submission_results_submission_id'), table_name='submission_results')
    op.drop_table('submission_results')

    op.drop_index(op.f('ix_judge_jobs_worker_id'), table_name='judge_jobs')
    op.drop_index(op.f('ix_judge_jobs_submission_id'), table_name='judge_jobs')
    op.drop_index('ix_judge_jobs_status_queued_at', table_name='judge_jobs')
    op.drop_index(op.f('ix_judge_jobs_status'), table_name='judge_jobs')
    op.drop_index(op.f('ix_judge_jobs_heartbeat_at'), table_name='judge_jobs')
    op.drop_index('ix_judge_jobs_heartbeat', table_name='judge_jobs')
    op.drop_table('judge_jobs')
