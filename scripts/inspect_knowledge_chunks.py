from pathlib import Path

from src.knowledge.chunker import chunk_knowledge_documents
from src.knowledge.loader import load_knowledge_directory
from src.knowledge.validator import validate_knowledge_collection


KNOWLEDGE_ROOT = Path("knowledge")


def main() -> None:
    documents = load_knowledge_directory(KNOWLEDGE_ROOT)

    validate_knowledge_collection(
        documents,
        knowledge_root=KNOWLEDGE_ROOT,
    )

    chunks = chunk_knowledge_documents(documents)

    print()
    print("Knowledge chunk inspection")
    print(f"Documents: {len(documents)}")
    print(f"Published chunks: {len(chunks)}")
    print()

    for chunk in chunks:
        print("=" * 72)
        print(f"ID:       {chunk.id}")
        print(f"Document: {chunk.document_id}")
        print(f"Heading:  {chunk.heading}")
        print(f"Topic:    {chunk.topic}")
        print(f"Hash:     {chunk.content_hash[:12]}...")
        print()
        print(chunk.content)
        print()


if __name__ == "__main__":
    main()