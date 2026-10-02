from __future__ import annotations

from dataclasses import dataclass

from src.knowledge.schema import KnowledgeEvidence
from src.knowledge.vector_store import KnowledgeIndex


@dataclass(frozen=True)
class RetrievalConfig:
    top_k: int = 5
    minimum_score: float = 0.30


class KnowledgeRetriever:
    """
    Application-level knowledge retrieval service.

    This is the boundary between vector-search infrastructure
    and the rest of the application.

    Agents consume KnowledgeEvidence and never interact directly
    with FAISS or embedding models.
    """

    def __init__(
        self,
        index: KnowledgeIndex,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.index = index
        self.config = config or RetrievalConfig()

        if self.config.top_k <= 0:
            raise ValueError(
                "Retrieval top_k must be greater than zero."
            )

        if not -1.0 <= self.config.minimum_score <= 1.0:
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
            top_k=self.config.top_k,
        )

        evidence: list[KnowledgeEvidence] = []

        for result in candidates:
            if result.score < self.config.minimum_score:
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
                    source_path=str(chunk.source_path),
                )
            )

        return evidence