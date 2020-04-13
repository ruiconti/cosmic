"""Alter ETA batches column

Revision ID: 245d1d308d9a
Revises: 9ed11becc823
Create Date: 2020-04-11 16:21:04.351013

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "245d1d308d9a"
down_revision = "9ed11becc823"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "batches", "eta", existing_type=postgresql.TIMESTAMP(), nullable=True
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "batches", "eta", existing_type=postgresql.TIMESTAMP(), nullable=False
    )
    # ### end Alembic commands ###
