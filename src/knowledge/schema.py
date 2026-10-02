from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

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