"""add idempotency records

Revision ID: 32cae35558bf
Revises: 79aef530a462
Create Date: 2026-10-02 10:11:40.670865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '32cae35558bf'
down_revision: Union[str, Sequence[str], None] = '79aef530a462'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    op.create_table(
        "idempotency_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "action_id",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "action_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "result",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "user_id",
            "action_id",
            name="uq_idempotency_user_action",
        ),
    )

    op.create_index(
        op.f(
            "ix_idempotency_records_user_id"
        ),
        "idempotency_records",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_idempotency_records_user_id"
        ),
        table_name="idempotency_records",
    )

    op.drop_table(
        "idempotency_records"
    )
