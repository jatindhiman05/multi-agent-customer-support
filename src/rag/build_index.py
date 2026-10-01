from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer


KNOWLEDGE_BASE_DIR = Path("data/knowledge_base")
INDEX_DIR = Path("data/faiss_index")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def build_index():
    documents = []

    for path in KNOWLEDGE_BASE_DIR.glob("*.md"):
        documents.append(
            {
                "content": path.read_text(encoding="utf-8"),
                "source": path.name,
            }
        )

    if not documents:
        raise RuntimeError("No knowledge base documents found.")

    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [doc["content"] for doc in documents]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
    )

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(
        index,
        str(INDEX_DIR / "index.faiss"),
    )

    with open(
        INDEX_DIR / "documents.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(documents, file, indent=2)

    print(f"Indexed {len(documents)} knowledge base documents.")
    print(f"FAISS index saved to: {INDEX_DIR}")


if __name__ == "__main__":
    build_index()