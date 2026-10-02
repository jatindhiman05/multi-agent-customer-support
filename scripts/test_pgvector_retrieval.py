from __future__ import annotations

from src.db.session import SessionLocal
from src.knowledge.embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from src.knowledge.retriever import (
    KnowledgeRetriever,
    RetrievalConfig,
)
from src.knowledge.vector_store import (
    PgVectorKnowledgeIndex,
)


def main() -> None:
    embedding_provider = (
        SentenceTransformerEmbeddingProvider()
    )

    with SessionLocal() as session:
        index = PgVectorKnowledgeIndex(
            session=session,
            embedding_provider=embedding_provider,
        )

        retriever = KnowledgeRetriever(
            index=index,
            config=RetrievalConfig(
                top_k=3,
                minimum_score=0.30,
            ),
        )

        query = (
            "Does the warranty cover accidental damage?"
        )

        evidence = retriever.retrieve(query)

        print()
        print(f"Query: {query}")
        print()

        for position, item in enumerate(
            evidence,
            start=1,
        ):
            print(
                f"{position}. "
                f"{item.chunk_id} "
                f"({item.score:.4f})"
            )
            print(
                f"   {item.title} > "
                f"{item.heading}"
            )
            print()


if __name__ == "__main__":
    main()