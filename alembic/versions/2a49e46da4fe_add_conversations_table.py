"""add conversations table

Revision ID: 2a49e46da4fe
Revises: 7ef42c9a658f
Create Date: 2026-10-01 22:49:15.181547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2a49e46da4fe'
down_revision: Union[str, Sequence[str], None] = '7ef42c9a658f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass