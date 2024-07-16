"""Update schema to match models

Revision ID: 3473d83a1c1f
Revises: 01719a6cf9c3
Create Date: 2024-06-19 15:34:43.073119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '3473d83a1c1f'
down_revision: Union[str, None] = '01719a6cf9c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('parkingslotbooking', sa.Column('vehicle_id', sa.Integer(), nullable=True))
    op.add_column('parkingslotbooking', sa.Column('parking_in_time', sa.DateTime(), nullable=True))
    op.add_column('parkingslotbooking', sa.Column('parking_out_time', sa.DateTime(), nullable=True))
    op.add_column('parkingslotbooking', sa.Column('fees', sa.Float(), nullable=True))
    op.add_column('parkingslotbooking', sa.Column('status', mysql.TINYINT(), nullable=True, comment=" '1:Active', '-1:Inactive', '0:Delete' "))
    op.drop_index('ix_parkingslotbooking_id', table_name='parkingslotbooking')
    op.create_foreign_key(None, 'parkingslotbooking', 'vehicle', ['vehicle_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'parkingslotbooking', type_='foreignkey')
    op.create_index('ix_parkingslotbooking_id', 'parkingslotbooking', ['id'], unique=False)
    op.drop_column('parkingslotbooking', 'status')
    op.drop_column('parkingslotbooking', 'fees')
    op.drop_column('parkingslotbooking', 'parking_out_time')
    op.drop_column('parkingslotbooking', 'parking_in_time')
    op.drop_column('parkingslotbooking', 'vehicle_id')
    # ### end Alembic commands ###
