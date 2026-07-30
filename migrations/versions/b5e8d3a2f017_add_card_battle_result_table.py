"""add card_battle_result table

Revision ID: b5e8d3a2f017
Revises: a3f7c2d1e894
Create Date: 2026-07-30 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5e8d3a2f017'
down_revision = 'a3f7c2d1e894'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'card_battle_result',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player1_id', sa.Integer(), nullable=True),
        sa.Column('player2_id', sa.Integer(), nullable=True),
        sa.Column('player1_won', sa.Boolean(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('played_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['player1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['player2_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('card_battle_result')
