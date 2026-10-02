from __future__ import annotations

from datetime import date, datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class KnowledgeChunkRecord(Base):
    """
    Persisted semantic-search representation of an authoritative
    knowledge chunk.

    The authoritative source remains the Markdown knowledge base.
    This table is a rebuildable retrieval index.
    """

    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    document_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    heading: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    last_reviewed: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    owner: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    embedding_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    source_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )