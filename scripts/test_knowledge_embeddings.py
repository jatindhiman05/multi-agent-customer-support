from src.knowledge.embeddings import (
    SentenceTransformerEmbeddingProvider,
)


def main() -> None:
    provider = SentenceTransformerEmbeddingProvider()

    texts = [
        "VoltNest accepts eligible returns within 30 days.",
        "Customers can return eligible products for thirty days.",
        "The weather is sunny today.",
    ]

    embeddings = provider.embed_documents(texts)

    print()
    print("Embedding provider test")
    print(f"Model: {provider.model_name}")
    print(f"Dimension: {provider.dimension}")
    print(f"Shape: {embeddings.shape}")

    similar_score = float(
        embeddings[0] @ embeddings[1]
    )

    unrelated_score = float(
        embeddings[0] @ embeddings[2]
    )

    print()
    print(
        "Return-vs-return similarity:",
        round(similar_score, 4),
    )

    print(
        "Return-vs-weather similarity:",
        round(unrelated_score, 4),
    )

    assert embeddings.shape == (
        len(texts),
        provider.dimension,
    )

    assert similar_score > unrelated_score

    print()
    print("Embedding test PASSED")


if __name__ == "__main__":
    main()