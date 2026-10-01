from langchain_core.tools import tool

from src.rag.retriever import retrieve_knowledge


@tool
def search_knowledge_base(query: str) -> dict:
    """
    Search VoltNest's knowledge base for policies, shipping information,
    warranty information, FAQs, and other company documentation.

    Use this tool when answering questions about VoltNest policies
    or general company information.
    """

    results = retrieve_knowledge(
        query=query,
        k=2,
    )

    return {
        "success": True,
        "results": results,
    }