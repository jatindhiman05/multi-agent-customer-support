from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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


@dataclass(frozen=True)
class EvaluationCase:
    query: str
    expected_chunk_ids: frozenset[str]


CASES = [
    EvaluationCase(
        query="How many days do I have to return a product?",
        expected_chunk_ids=frozenset(
            {
                "returns-policy:overview",
                "returns-policy:eligibility",
                "returns-policy:non-returnable-items",
            }
        ),
    ),
    EvaluationCase(
        query="What is the return window?",
        expected_chunk_ids=frozenset(
            {
                "returns-policy:overview",
                "returns-policy:eligibility",
                "returns-policy:non-returnable-items",
            }
        ),
    ),
    EvaluationCase(
        query="How long does the warranty last?",
        expected_chunk_ids=frozenset(
            {
                "warranty-policy:overview",
            }
        ),
    ),
    EvaluationCase(
        query="Does the warranty cover accidental damage?",
        expected_chunk_ids=frozenset(
            {
                "warranty-policy:not-covered",
            }
        ),
    ),
    EvaluationCase(
        query="Can I cancel something that has already shipped?",
        expected_chunk_ids=frozenset(
            {
                "cancellations-policy:shipped-orders",
            }
        ),
    ),
    EvaluationCase(
        query="Do I need to confirm before my order is cancelled?",
        expected_chunk_ids=frozenset(
            {
                "cancellations-policy:confirmation",
            }
        ),
    ),
    EvaluationCase(
        query="My tracking says delivered but the parcel is missing.",
        expected_chunk_ids=frozenset(
            {
                "lost-packages-policy:delivered-but-not-found",
            }
        ),
    ),
    EvaluationCase(
        query="My shipment is late. Does that mean it is lost?",
        expected_chunk_ids=frozenset(
            {
                "lost-packages-policy:overview",
                "lost-packages-policy:delayed-shipments",
                "shipping-policy:shipping-delays",
            }
        ),
    ),
    EvaluationCase(
        query="How long until my refund shows in my bank?",
        expected_chunk_ids=frozenset(
            {
                "refunds-policy:refund-processing",
                "returns-policy:refunds",
            }
        ),
    ),
    EvaluationCase(
        query="Where does my refund get sent?",
        expected_chunk_ids=frozenset(
            {
                "refunds-policy:overview",
                "refunds-policy:original-payment-method",
            }
        ),
    ),
    EvaluationCase(
    query="What should I do if my product arrived damaged?",
    expected_chunk_ids=frozenset(
        {
            "damaged-items-policy:overview",
            "damaged-items-policy:what-to-provide",
            "damaged-items-policy:packaging",
            "returns-policy:damaged-or-incorrect-items",
        }
    ),
),
    EvaluationCase(
        query="Should I keep using a product that seems unsafe?",
        expected_chunk_ids=frozenset(
            {
                "damaged-items-policy:safety-concerns",
            }
        ),
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

    chunks = chunk_knowledge_documents(documents)

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

    passed = 0

    print()
    print("VoltNest knowledge retrieval evaluation")
    print(f"Cases: {len(CASES)}")
    print()

    for number, case in enumerate(CASES, start=1):
        results = retriever.retrieve(case.query)

        returned_ids = [
            result.chunk_id
            for result in results
        ]

        matched = any(
            chunk_id in case.expected_chunk_ids
            for chunk_id in returned_ids
        )

        status = "PASS" if matched else "FAIL"

        if matched:
            passed += 1

        print(
            f"[{status}] {number}. {case.query}"
        )

        for rank, result in enumerate(
            results,
            start=1,
        ):
            marker = (
                "*"
                if result.chunk_id
                in case.expected_chunk_ids
                else " "
            )

            print(
                f"    {marker} {rank}. "
                f"{result.chunk_id} "
                f"({result.score:.4f})"
            )

        print()

    accuracy = passed / len(CASES)

    print("=" * 72)
    print(
        f"Passed: {passed}/{len(CASES)} "
        f"({accuracy:.1%})"
    )

    if passed != len(CASES):
        raise SystemExit(1)

    print("Knowledge retrieval evaluation PASSED")


if __name__ == "__main__":
    main()