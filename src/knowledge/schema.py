from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal,Any

from pydantic import BaseModel, ConfigDict, Field


KnowledgeCategory = Literal[
    "policies",
    "orders",
    "payments",
    "products",
    "account",
    "company",
]

KnowledgeStatus = Literal[
    "draft",
    "published",
    "archived",
]


class KnowledgeDocument(BaseModel):
    """
    Canonical representation of an authoritative VoltNest knowledge document.

    Markdown files are converted into this model before they are allowed
    into the retrieval/indexing pipeline.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)

    category: KnowledgeCategory
    topic: str = Field(min_length=1)

    version: str = Field(min_length=1)
    status: KnowledgeStatus

    effective_date: date
    last_reviewed: date

    owner: str = Field(min_length=1)

    content: str = Field(min_length=1)
    source_path: Path

class KnowledgeChunk(BaseModel):
    """
    Retrieval-ready unit derived from an authoritative knowledge document.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)

    chunk_index: int = Field(ge=0)

    title: str = Field(min_length=1)
    heading: str = Field(min_length=1)

    category: KnowledgeCategory
    topic: str = Field(min_length=1)

    version: str = Field(min_length=1)
    status: KnowledgeStatus

    effective_date: date
    last_reviewed: date

    owner: str = Field(min_length=1)

    content: str = Field(min_length=1)
    content_hash: str = Field(min_length=64, max_length=64)

    source_path: Path

    def retrieval_metadata(self) -> dict[str, Any]:
        return {
            "chunk_id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "title": self.title,
            "heading": self.heading,
            "category": self.category,
            "topic": self.topic,
            "version": self.version,
            "status": self.status,
            "effective_date": self.effective_date.isoformat(),
            "last_reviewed": self.last_reviewed.isoformat(),
            "owner": self.owner,
            "content_hash": self.content_hash,
            "source": self.source_path.as_posix(),
        }