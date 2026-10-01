from src.rag.retriever import retrieve_knowledge


queries = [
    "How long do I have to return a product?",
    "Does the warranty cover accidental damage?",
    "What should I do if my package says delivered but I cannot find it?",
]


for query in queries:
    print("\n" + "=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)

    results = retrieve_knowledge(query)

    for index, result in enumerate(results, start=1):
        print(f"\nRESULT {index}")
        print(f"Source: {result['source']}")
        print(f"Score: {result['score']:.4f}")
        print(result["content"])