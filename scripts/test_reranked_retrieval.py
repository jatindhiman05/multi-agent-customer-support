from __future__ import annotations

from src.db.session import SessionLocal
from src.knowledge.embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from src.knowledge.reranker import (
    CrossEncoderKnowledgeReranker,
)
from src.knowledge.retriever import (
    KnowledgeRetriever,
    RetrievalConfig,
)
from src.knowledge.vector_store import (
    PgVectorKnowledgeIndex,
)


QUERY = (
    "Does the VoltNest warranty cover "
    "accidental damage?"
)


def main() -> None:
    embedding_provider = (
        SentenceTransformerEmbeddingProvider()
    )

    reranker = CrossEncoderKnowledgeReranker()

    with SessionLocal() as session:
        index = PgVectorKnowledgeIndex(
            session=session,
            embedding_provider=embedding_provider,
        )

        retriever = KnowledgeRetriever(
            index=index,
            reranker=reranker,
            config=RetrievalConfig(
                candidate_k=10,
                top_k=3,
                minimum_score=None,
            ),
        )

        evidence = retriever.retrieve(
            QUERY
        )

    print()
    print(f"Query: {QUERY}")
    print()
    print("=== RERANKED TOP 3 ===")

    for rank, item in enumerate(
        evidence,
        start=1,
    ):
        print(
            f"{rank}. "
            f"{item.chunk_id} | "
            f"{item.score:.4f} | "
            f"{item.heading}"
        )


if __name__ == "__main__":
    main()