from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

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


@lru_cache(maxsize=1)
def get_knowledge_retriever() -> KnowledgeRetriever:
    """
    Build the application knowledge retriever once per process.

    The current implementation uses an in-memory FAISS index.
    The KnowledgeRetriever boundary allows the underlying vector
    storage implementation to be replaced later without changing
    the agent or tool contract.
    """

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

    return KnowledgeRetriever(
        index=index,
        config=RetrievalConfig(
            top_k=3,
            minimum_score=0.30,
        ),
    )


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

    retriever = get_knowledge_retriever()

    evidence = retriever.retrieve(query)

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