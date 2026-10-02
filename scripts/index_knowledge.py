from __future__ import annotations

from src.db.session import SessionLocal
from src.knowledge.chunker import (
    chunk_knowledge_documents,
)
from src.knowledge.embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from src.knowledge.indexer import KnowledgeIndexer
from src.knowledge.loader import (
    load_knowledge_directory,
)


KNOWLEDGE_ROOT = "knowledge"


def main() -> None:
    print("Loading knowledge documents...")

    documents = load_knowledge_directory(
        KNOWLEDGE_ROOT
    )

    print(
        f"Loaded {len(documents)} documents."
    )

    chunks = chunk_knowledge_documents(
        documents
    )

    print(
        f"Generated {len(chunks)} published chunks."
    )

    print("Loading embedding model...")

    embedding_provider = (
        SentenceTransformerEmbeddingProvider()
    )

    print(
        "Embedding model: "
        f"{embedding_provider.model_name}"
    )

    print(
        "Embedding dimension: "
        f"{embedding_provider.dimension}"
    )

    with SessionLocal() as session:
        try:
            indexer = KnowledgeIndexer(
                session=session,
                embedding_provider=embedding_provider,
            )

            stats = indexer.sync(chunks)

            session.commit()

        except Exception:
            session.rollback()
            raise

    print()
    print("Knowledge index synchronization complete.")
    print(f"Inserted:  {stats.inserted}")
    print(f"Updated:   {stats.updated}")
    print(f"Unchanged: {stats.unchanged}")
    print(f"Deleted:   {stats.deleted}")
    print(f"Embedded:  {stats.embedded}")


if __name__ == "__main__":
    main()