from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.knowledge.chunker import chunk_knowledge_documents
from src.knowledge.embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from src.knowledge.loader import load_knowledge_directory
from src.knowledge.retriever import (
    KnowledgeRetriever,
    RetrievalConfig,
)
from src.knowledge.validator import validate_knowledge_collection
from src.knowledge.vector_store import FAISSKnowledgeIndex


KNOWLEDGE_ROOT = Path("knowledge")

QueryType = Literal[
    "static_knowledge",
    "live_data",
    "out_of_scope",
]


@dataclass(frozen=True)
class BoundaryCase:
    query: str
    query_type: QueryType


CASES = [
    # ---------------------------------------------------------
    # STATIC COMPANY KNOWLEDGE
    # ---------------------------------------------------------
    BoundaryCase(
        query="What is VoltNest's return policy?",
        query_type="static_knowledge",
    ),
    BoundaryCase(
        query="How does the warranty work?",
        query_type="static_knowledge",
    ),
    BoundaryCase(
        query="Can shipped orders normally be cancelled?",
        query_type="static_knowledge",
    ),
    BoundaryCase(
        query="How are refunds processed?",
        query_type="static_knowledge",
    ),

    # ---------------------------------------------------------
    # LIVE CUSTOMER / ORDER DATA
    # ---------------------------------------------------------
    BoundaryCase(
        query="Where is order ORD-1003?",
        query_type="live_data",
    ),
    BoundaryCase(
        query="Can I return ORD-1004?",
        query_type="live_data",
    ),
    BoundaryCase(
        query="Cancel ORD-1006.",
        query_type="live_data",
    ),
    BoundaryCase(
        query="Has my refund for ORD-1002 been processed?",
        query_type="live_data",
    ),

    # ---------------------------------------------------------
    # OUT OF SCOPE
    # ---------------------------------------------------------
    BoundaryCase(
        query="What is the capital of France?",
        query_type="out_of_scope",
    ),
    BoundaryCase(
        query="Write me a Python sorting algorithm.",
        query_type="out_of_scope",
    ),
    BoundaryCase(
        query="Who won the football match yesterday?",
        query_type="out_of_scope",
    ),
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

    retriever = KnowledgeRetriever(
        index=index,
        config=RetrievalConfig(
            top_k=3,
            minimum_score=0.30,
        ),
    )

    print()
    print("VoltNest knowledge boundary evaluation")
    print()

    for case in CASES:
        results = retriever.retrieve(case.query)

        print("=" * 72)
        print(f"TYPE:  {case.query_type}")
        print(f"QUERY: {case.query}")

        if not results:
            print("RESULT: no evidence above threshold")
            print()
            continue

        print()

        for rank, result in enumerate(
            results,
            start=1,
        ):
            print(
                f"{rank}. "
                f"{result.chunk_id} "
                f"({result.score:.4f})"
            )

        print()


if __name__ == "__main__":
    main()