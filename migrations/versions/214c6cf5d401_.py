"""empty message

Revision ID: 214c6cf5d401
Revises: c3eb68195da4
Create Date: 2019-10-23 12:40:14.702253

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '214c6cf5d401'
down_revision = 'c3eb68195da4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('Address_venue_id_fkey', 'Address', type_='foreignkey')
    op.create_foreign_key(None, 'Address', 'Venue', ['venue_id'], ['id'], onupdate='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'Address', type_='foreignkey')
    op.create_foreign_key('Address_venue_id_fkey', 'Address', 'Venue', ['venue_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    # ### end Alembic commands ###
