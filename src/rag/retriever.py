import json

import faiss
from sentence_transformers import SentenceTransformer

from src.rag.build_index import EMBEDDING_MODEL, INDEX_DIR


model = SentenceTransformer(EMBEDDING_MODEL)

index = faiss.read_index(
    str(INDEX_DIR / "index.faiss")
)

with open(
    INDEX_DIR / "documents.json",
    "r",
    encoding="utf-8",
) as file:
    documents = json.load(file)


def retrieve_knowledge(
    query: str,
    k: int = 2,
) -> list[dict]:

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )

    scores, indices = index.search(
        query_embedding,
        min(k, len(documents)),
    )

    results = []

    for score, document_index in zip(
        scores[0],
        indices[0],
    ):
        document = documents[document_index]

        results.append(
            {
                "content": document["content"],
                "source": document["source"],
                "score": float(score),
            }
        )

    return results