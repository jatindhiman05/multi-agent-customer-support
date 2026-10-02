"""add pgvector knowledge chunks

Revision ID: 77867338e83b
Revises: 4d6591c685e9
Create Date: 2026-10-02 17:35:53.000382
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR


# revision identifiers, used by Alembic.
revision: str = "77867338e83b"
down_revision: Union[str, Sequence[str], None] = "4d6591c685e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create persistent pgvector-backed knowledge storage."""

    # pgvector must exist before PostgreSQL can create VECTOR columns.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("document_id", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("heading", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("last_reviewed", sa.Date(), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("embedding", VECTOR(dim=384), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_knowledge_chunks_category"),
        "knowledge_chunks",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_chunks_content_hash"),
        "knowledge_chunks",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_chunks_document_id"),
        "knowledge_chunks",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_chunks_status"),
        "knowledge_chunks",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_chunks_topic"),
        "knowledge_chunks",
        ["topic"],
        unique=False,
    )


def downgrade() -> None:
    """Remove persistent knowledge storage."""

    op.drop_index(
        op.f("ix_knowledge_chunks_topic"),
        table_name="knowledge_chunks",
    )
    op.drop_index(
        op.f("ix_knowledge_chunks_status"),
        table_name="knowledge_chunks",
    )
    op.drop_index(
        op.f("ix_knowledge_chunks_document_id"),
        table_name="knowledge_chunks",
    )
    op.drop_index(
        op.f("ix_knowledge_chunks_content_hash"),
        table_name="knowledge_chunks",
    )
    op.drop_index(
        op.f("ix_knowledge_chunks_category"),
        table_name="knowledge_chunks",
    )

    op.drop_table("knowledge_chunks")