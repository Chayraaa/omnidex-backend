"""add wbr_play table

Revision ID: c9a1f4b6e230
Revises: b5e8d3a2f017
Create Date: 2026-07-30 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9a1f4b6e230'
down_revision = 'b5e8d3a2f017'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'wbr_play',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('streak', sa.Integer(), nullable=False),
        sa.Column('highscore', sa.Integer(), nullable=False),
        sa.Column('won', sa.Boolean(), nullable=False),
        sa.Column('played_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('wbr_play')
