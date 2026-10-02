from pathlib import Path

from src.knowledge.chunker import chunk_knowledge_documents
from src.knowledge.embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from src.knowledge.loader import load_knowledge_directory
from src.knowledge.validator import validate_knowledge_collection
from src.knowledge.vector_store import FAISSKnowledgeIndex


KNOWLEDGE_ROOT = Path("knowledge")


TEST_QUERIES = [
    "How long do I have to return something?",
    "How long is the warranty?",
    "Can I cancel an order that has already shipped?",
    "My package says delivered but I cannot find it.",
    "When will my refund appear in my bank account?",
]


def main() -> None:
    documents = load_knowledge_directory(
        KNOWLEDGE_ROOT
    )

    validate_knowledge_collection(
        documents,
        knowledge_root=KNOWLEDGE_ROOT,
    )

    chunks = chunk_knowledge_documents(
        documents
    )

    embedding_provider = (
        SentenceTransformerEmbeddingProvider()
    )

    index = FAISSKnowledgeIndex(
        embedding_provider=embedding_provider
    )

    index.build(chunks)

    print()
    print("VoltNest knowledge search")
    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")
    print(f"Index vectors: {index.size}")

    for query in TEST_QUERIES:
        print()
        print("=" * 72)
        print(f"QUERY: {query}")
        print()

        results = index.search(
            query,
            top_k=3,
        )

        for rank, result in enumerate(
            results,
            start=1,
        ):
            print(
                f"{rank}. "
                f"{result.chunk.id} "
                f"(score={result.score:.4f})"
            )

            print(
                f"   {result.chunk.heading}"
            )

            preview = (
                result.chunk.content
                .replace("\n", " ")
            )

            print(
                f"   {preview[:180]}"
            )


if __name__ == "__main__":
    main()