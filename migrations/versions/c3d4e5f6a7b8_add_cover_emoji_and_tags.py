"""add cover_emoji to study_set and add tag + study_set_tag tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-17 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('study_set') as batch_op:
        batch_op.add_column(sa.Column('cover_emoji', sa.String(length=8), nullable=True))

    op.create_table(
        'tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_tag_name'), 'tag', ['name'], unique=False)

    op.create_table(
        'study_set_tag',
        sa.Column('study_set_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['study_set_id'], ['study_set.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id']),
        sa.PrimaryKeyConstraint('study_set_id', 'tag_id'),
    )


def downgrade():
    op.drop_table('study_set_tag')
    op.drop_index(op.f('ix_tag_name'), table_name='tag')
    op.drop_table('tag')
    with op.batch_alter_table('study_set') as batch_op:
        batch_op.drop_column('cover_emoji')
