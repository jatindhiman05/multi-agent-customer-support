from __future__ import annotations

from functools import lru_cache

from langchain_core.tools import tool

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


@lru_cache(maxsize=1)
def get_reranker() -> (
    CrossEncoderKnowledgeReranker
):
    """
    Load the knowledge reranker once per application process.

    The model is expensive to initialize but safe to reuse across
    retrieval operations.
    """

    return CrossEncoderKnowledgeReranker()


def retrieve_knowledge(
    query: str,
):
    """
    Retrieve authoritative VoltNest knowledge from PostgreSQL.

    Retrieval uses pgvector for broad candidate generation followed
    by cross-encoder reranking for final evidence selection.

    A fresh SQLAlchemy session is created for each retrieval operation.
    The underlying engine manages connection pooling.
    """

    embedding_provider = get_embedding_provider()
    reranker = get_reranker()

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

        return retriever.retrieve(query)


@tool
def search_knowledge_base(
    query: str,
) -> dict:
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