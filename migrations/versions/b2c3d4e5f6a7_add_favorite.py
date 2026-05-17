"""add favorite table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-17 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'favorite',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('study_set_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['study_set_id'], ['study_set.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'study_set_id', name='uq_favorite_user_set'),
    )
    op.create_index(op.f('ix_favorite_user_id'), 'favorite', ['user_id'], unique=False)
    op.create_index(op.f('ix_favorite_study_set_id'), 'favorite', ['study_set_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_favorite_study_set_id'), table_name='favorite')
    op.drop_index(op.f('ix_favorite_user_id'), table_name='favorite')
    op.drop_table('favorite')
