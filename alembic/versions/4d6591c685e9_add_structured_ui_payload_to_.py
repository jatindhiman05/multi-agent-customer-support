"""add structured ui payload to conversation messages

Revision ID: 4d6591c685e9
Revises: 937d9213d75d
Create Date: 2026-10-02 14:29:32.629347

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d6591c685e9'
down_revision: Union[str, Sequence[str], None] = '937d9213d75d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column(
            "ui_payload",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "conversation_messages",
        "ui_payload",
    )