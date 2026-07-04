"""add_performance_indices

Revision ID: 6754fe0119f3
Revises: db0495044408
Create Date: 2026-07-01 17:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6754fe0119f3'
down_revision: Union[str, None] = 'db0495044408'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    pass


def downgrade():
    pass
