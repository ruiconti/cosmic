"""Sets up allocations view

Revision ID: 25b0aad777c6
Revises: 245d1d308d9a
Create Date: 2020-04-14 14:55:05.800107

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "25b0aad777c6"
down_revision = "245d1d308d9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "allocations_view",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_orderline", sa.String(length=255), nullable=True),
        sa.Column("batchref", sa.String(length=255), nullable=True),
        sa.Column("sku", sa.String(length=255), nullable=True),
        sa.Column("qty", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("allocations_view")
