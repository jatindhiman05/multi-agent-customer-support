"""add failed chat request status

Revision ID: 8224977d4631
Revises: c95722c4b1fb
Create Date: 2026-10-04 19:13:29.312968
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8224977d4631"
down_revision: Union[str, Sequence[str], None] = (
    "c95722c4b1fb"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_chat_request_status",
        "chat_request_records",
        type_="check",
    )

    op.create_check_constraint(
        "ck_chat_request_status",
        "chat_request_records",
        "status IN ('processing', 'completed', 'failed')",
    )


def downgrade() -> None:
    # A downgrade cannot safely restore the old constraint
    # while failed rows exist, because PostgreSQL would reject
    # the constraint. Convert them back to processing first.
    op.execute(
        """
        UPDATE chat_request_records
        SET status = 'processing'
        WHERE status = 'failed'
        """
    )

    op.drop_constraint(
        "ck_chat_request_status",
        "chat_request_records",
        type_="check",
    )

    op.create_check_constraint(
        "ck_chat_request_status",
        "chat_request_records",
        "status IN ('processing', 'completed')",
    )