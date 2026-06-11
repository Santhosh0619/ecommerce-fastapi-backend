"""add_product_rating_columns_and_review_uq

Revision ID: 7b0a8f1e6d2c
Revises: 350facfff45e
Create Date: 2026-06-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b0a8f1e6d2c'
down_revision: Union[str, Sequence[str], None] = '350facfff45e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('average_rating', sa.DECIMAL(precision=3, scale=2), server_default='0.00', nullable=False))
    op.add_column('products', sa.Column('review_count', sa.Integer(), server_default='0', nullable=False))
    op.create_unique_constraint('uq_review_user_product', 'reviews', ['user_id', 'product_id'])


def downgrade() -> None:
    op.drop_constraint('uq_review_user_product', 'reviews', type_='unique')
    op.drop_column('products', 'review_count')
    op.drop_column('products', 'average_rating')
