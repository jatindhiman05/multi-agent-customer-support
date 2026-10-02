from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class EmbeddingProvider(ABC):
    """
    Interface used by the knowledge system to generate embeddings.

    Retrieval code must depend on this abstraction rather than directly
    depending on SentenceTransformers.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_documents(
        self,
        texts: list[str],
    ) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def embed_query(
        self,
        text: str,
    ) -> np.ndarray:
        raise NotImplementedError


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    Local sentence-transformers embedding implementation.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        self.model_name = model_name

        self._model = SentenceTransformer(model_name)

        dimension = self._model.get_embedding_dimension()

        if dimension is None:
            raise ValueError(
                f"Embedding model '{model_name}' did not report "
                "an embedding dimension."
            )

        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(
        self,
        texts: list[str],
    ) -> np.ndarray:
        if not texts:
            return np.empty(
                (0, self.dimension),
                dtype=np.float32,
            )

        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(
            embeddings,
            dtype=np.float32,
        )

    def embed_query(
        self,
        text: str,
    ) -> np.ndarray:
        if not text.strip():
            raise ValueError(
                "Query text cannot be empty."
            )

        embedding = self._model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(
            embedding,
            dtype=np.float32,
        )