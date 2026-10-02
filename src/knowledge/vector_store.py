from __future__ import annotations

from abc import ABC, abstractmethod

import faiss
import numpy as np
from sqlalchemy.orm import Session

from src.repositories.knowledge_chunk_repository import (
    KnowledgeChunkRepository,
)
from src.knowledge.embeddings import EmbeddingProvider
from src.knowledge.schema import (
    KnowledgeChunk,
    KnowledgeSearchResult,
)


class KnowledgeIndex(ABC):
    """
    Storage-independent interface for semantic knowledge search.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[KnowledgeSearchResult]:
        raise NotImplementedError

class FAISSKnowledgeIndex(KnowledgeIndex):
    """
    In-memory FAISS implementation using normalized embeddings and
    inner-product similarity.

    Because embeddings are normalized, inner product is equivalent
    to cosine similarity.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.embedding_provider = embedding_provider

        self._index: faiss.Index | None = None
        self._chunks: list[KnowledgeChunk] = []

    @property
    def size(self) -> int:
        return len(self._chunks)

    def build(
        self,
        chunks: list[KnowledgeChunk],
    ) -> None:
        if not chunks:
            raise ValueError(
                "Cannot build knowledge index without chunks."
            )

        contents = [
            chunk.embedding_text
            for chunk in chunks
        ]
        embeddings = self.embedding_provider.embed_documents(
            contents
        )

        expected_shape = (
            len(chunks),
            self.embedding_provider.dimension,
        )

        if embeddings.shape != expected_shape:
            raise ValueError(
                "Unexpected embedding matrix shape. "
                f"Expected {expected_shape}, "
                f"received {embeddings.shape}."
            )

        embeddings = np.ascontiguousarray(
            embeddings,
            dtype=np.float32,
        )

        index = faiss.IndexFlatIP(
            self.embedding_provider.dimension
        )

        index.add(embeddings)

        self._index = index
        self._chunks = list(chunks)

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[KnowledgeSearchResult]:
        if self._index is None:
            raise RuntimeError(
                "Knowledge index has not been built."
            )

        if not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if not self._chunks:
            return []

        query_embedding = (
            self.embedding_provider.embed_query(query)
        )

        query_embedding = np.ascontiguousarray(
            query_embedding.reshape(1, -1),
            dtype=np.float32,
        )

        result_count = min(
            top_k,
            len(self._chunks),
        )

        scores, indices = self._index.search(
            query_embedding,
            result_count,
        )

        results: list[KnowledgeSearchResult] = []

        for score, index_position in zip(
            scores[0],
            indices[0],
            strict=True,
        ):
            if index_position < 0:
                continue

            chunk = self._chunks[
                int(index_position)
            ]

            results.append(
                KnowledgeSearchResult(
                    chunk=chunk,
                    score=float(score),
                )
            )

        return results

class PgVectorKnowledgeIndex(KnowledgeIndex):
    """
    PostgreSQL/pgvector implementation of semantic knowledge search.

    Embeddings are persisted separately by KnowledgeIndexer.
    This class owns only the online read/search path.
    """

    EXPECTED_DIMENSION = 384

    def __init__(
        self,
        session: Session,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.repository = KnowledgeChunkRepository(
            session
        )

        if (
            self.embedding_provider.dimension
            != self.EXPECTED_DIMENSION
        ):
            raise ValueError(
                "Knowledge embedding dimension mismatch: "
                f"database expects "
                f"{self.EXPECTED_DIMENSION}, "
                f"but model "
                f"'{self.embedding_provider.model_name}' "
                f"produces "
                f"{self.embedding_provider.dimension}."
            )

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[KnowledgeSearchResult]:
        if not query.strip():
            raise ValueError(
                "Search query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query_embedding = (
            self.embedding_provider.embed_query(
                query
            )
        )

        if query_embedding.shape != (
            self.embedding_provider.dimension,
        ):
            raise ValueError(
                "Unexpected query embedding shape. "
                f"Expected "
                f"({self.embedding_provider.dimension},), "
                f"received "
                f"{query_embedding.shape}."
            )

        return self.repository.search_by_embedding(
            query_embedding.tolist(),
            embedding_model=(
                self.embedding_provider.model_name
            ),
            top_k=top_k,
        )