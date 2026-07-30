"""add timestamps to wbr and card battle

Revision ID: a3f7c2d1e894
Revises: 91a19a879b71
Create Date: 2026-07-30 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f7c2d1e894'
down_revision = '91a19a879b71'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('what_beats_rock', schema=None) as batch_op:
        batch_op.add_column(sa.Column('played_at', sa.DateTime(), nullable=True))

    with op.batch_alter_table('card_battle_game', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('card_battle_game', schema=None) as batch_op:
        batch_op.drop_column('created_at')

    with op.batch_alter_table('what_beats_rock', schema=None) as batch_op:
        batch_op.drop_column('played_at')
