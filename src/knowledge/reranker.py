from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from sentence_transformers import CrossEncoder

from src.knowledge.schema import KnowledgeSearchResult


DEFAULT_RERANKER_MODEL = (
    "cross-encoder/ms-marco-MiniLM-L6-v2"
)


class KnowledgeReranker(ABC):
    """
    Interface for second-stage knowledge reranking.

    A reranker receives candidates from the vector index and
    reorders them according to their relevance to the query.
    """

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[KnowledgeSearchResult],
    ) -> list[KnowledgeSearchResult]:
        raise NotImplementedError


class CrossEncoderKnowledgeReranker(
    KnowledgeReranker
):
    """
    Cross-encoder reranker for knowledge-search candidates.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_RERANKER_MODEL,
    ) -> None:
        self._model_name = model_name
        self._model = CrossEncoder(model_name)

    @property
    def model_name(self) -> str:
        return self._model_name

    def rerank(
        self,
        query: str,
        candidates: list[KnowledgeSearchResult],
    ) -> list[KnowledgeSearchResult]:
        if not query.strip():
            raise ValueError(
                "Reranking query cannot be empty."
            )

        if not candidates:
            return []

        pairs = [
            (
                query,
                candidate.chunk.embedding_text,
            )
            for candidate in candidates
        ]

        scores = self._model.predict(
            pairs,
            show_progress_bar=False,
        )

        scores = np.asarray(
            scores,
            dtype=np.float32,
        ).reshape(-1)

        if len(scores) != len(candidates):
            raise RuntimeError(
                "Reranker returned an unexpected "
                "number of scores."
            )

        reranked = [
            KnowledgeSearchResult(
                chunk=candidate.chunk,
                score=float(score),
            )
            for candidate, score in zip(
                candidates,
                scores,
                strict=True,
            )
        ]

        reranked.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return reranked