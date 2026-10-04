"""set null chat request conversation on delete

Revision ID: c95722c4b1fb
Revises: 4a51117503d3
Create Date: 2026-10-04 18:07:19.070350
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c95722c4b1fb"
down_revision: Union[str, Sequence[str], None] = "4a51117503d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT_NAME = "chat_request_records_conversation_id_fkey"


def upgrade() -> None:
    op.drop_constraint(
        CONSTRAINT_NAME,
        "chat_request_records",
        type_="foreignkey",
    )

    op.create_foreign_key(
        CONSTRAINT_NAME,
        "chat_request_records",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        CONSTRAINT_NAME,
        "chat_request_records",
        type_="foreignkey",
    )

    op.create_foreign_key(
        CONSTRAINT_NAME,
        "chat_request_records",
        "conversations",
        ["conversation_id"],
        ["id"],
    )