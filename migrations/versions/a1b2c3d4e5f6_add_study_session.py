"""add study_session table

Revision ID: a1b2c3d4e5f6
Revises: 8989b9ef1e85
Create Date: 2026-05-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '8989b9ef1e85'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'study_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('study_set_id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['study_set_id'], ['study_set.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_study_session_user_id'), 'study_session', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_study_session_study_set_id'), 'study_session', ['study_set_id'], unique=False
    )
    op.create_index(
        op.f('ix_study_session_finished_at'), 'study_session', ['finished_at'], unique=False
    )


def downgrade():
    op.drop_index(op.f('ix_study_session_finished_at'), table_name='study_session')
    op.drop_index(op.f('ix_study_session_study_set_id'), table_name='study_session')
    op.drop_index(op.f('ix_study_session_user_id'), table_name='study_session')
    op.drop_table('study_session')
