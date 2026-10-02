from __future__ import annotations

from dataclasses import dataclass

from src.knowledge.reranker import (
    KnowledgeReranker,
)
from src.knowledge.schema import (
    KnowledgeEvidence,
)
from src.knowledge.vector_store import (
    KnowledgeIndex,
)


@dataclass(frozen=True)
class RetrievalConfig:
    top_k: int = 5
    candidate_k: int = 10
    minimum_score: float | None = None


class KnowledgeRetriever:
    """
    Application-level knowledge retrieval service.

    Retrieval is performed in two stages:

    1. The vector index retrieves a broad candidate set.
    2. An optional reranker reorders those candidates.

    Agents consume KnowledgeEvidence and never interact directly
    with vector databases, embedding models, or reranking models.
    """

    def __init__(
        self,
        index: KnowledgeIndex,
        config: RetrievalConfig | None = None,
        reranker: KnowledgeReranker | None = None,
    ) -> None:
        self.index = index
        self.config = config or RetrievalConfig()
        self.reranker = reranker

        if self.config.top_k <= 0:
            raise ValueError(
                "Retrieval top_k must be greater than zero."
            )

        if self.config.candidate_k <= 0:
            raise ValueError(
                "Retrieval candidate_k must be greater than zero."
            )

        if (
            self.config.candidate_k
            < self.config.top_k
        ):
            raise ValueError(
                "candidate_k must be greater than or "
                "equal to top_k."
            )

        if (
            self.config.minimum_score is not None
            and not -1.0
            <= self.config.minimum_score
            <= 1.0
        ):
            raise ValueError(
                "minimum_score must be between -1 and 1."
            )

    def retrieve(
        self,
        query: str,
    ) -> list[KnowledgeEvidence]:
        if not query.strip():
            raise ValueError(
                "Knowledge retrieval query cannot be empty."
            )

        candidates = self.index.search(
            query,
            top_k=self.config.candidate_k,
        )

        if self.reranker is not None:
            candidates = self.reranker.rerank(
                query,
                candidates,
            )

        candidates = candidates[
            : self.config.top_k
        ]

        evidence: list[KnowledgeEvidence] = []

        for result in candidates:
            if (
                self.config.minimum_score is not None
                and result.score
                < self.config.minimum_score
            ):
                continue

            chunk = result.chunk

            evidence.append(
                KnowledgeEvidence(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    heading=chunk.heading,
                    content=chunk.content,
                    score=result.score,
                    category=chunk.category,
                    topic=chunk.topic,
                    version=chunk.version,
                    effective_date=chunk.effective_date,
                    source_path=str(
                        chunk.source_path
                    ),
                )
            )

        return evidence