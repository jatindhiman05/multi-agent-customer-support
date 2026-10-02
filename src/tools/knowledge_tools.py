from __future__ import annotations

from functools import lru_cache

from langchain_core.tools import tool

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


@lru_cache(maxsize=1)
def get_embedding_provider() -> (
    SentenceTransformerEmbeddingProvider
):
    """
    Load the embedding model once per application process.

    The model is expensive to initialize but safe to reuse for
    knowledge-query embedding generation.
    """

    return SentenceTransformerEmbeddingProvider()


def retrieve_knowledge(
    query: str,
):
    """
    Retrieve authoritative VoltNest knowledge from PostgreSQL.

    A fresh SQLAlchemy session is created for each retrieval operation.
    The underlying engine manages connection pooling.
    """

    embedding_provider = get_embedding_provider()

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

        return retriever.retrieve(query)


@tool
def search_knowledge_base(query: str) -> dict:
    """
    Search authoritative VoltNest static knowledge.

    Use this tool for general VoltNest policies, shipping rules,
    return rules, refund rules, warranty information, cancellation
    rules, damaged-item guidance, and lost-package guidance.

    This tool does not provide live customer, order, payment,
    shipment, refund, or account state.
    """

    evidence = retrieve_knowledge(query)

    return {
        "success": True,
        "evidence_found": bool(evidence),
        "evidence": [
            item.model_dump(
                mode="json"
            )
            for item in evidence
        ],
    }