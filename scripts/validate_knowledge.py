from pathlib import Path

from src.knowledge.loader import (
    KnowledgeLoadError,
    load_knowledge_directory,
)
from src.knowledge.validator import (
    KnowledgeValidationError,
    validate_knowledge_collection,
)


KNOWLEDGE_ROOT = Path("knowledge")


def main() -> None:
    try:
        documents = load_knowledge_directory(KNOWLEDGE_ROOT)

        validate_knowledge_collection(
            documents,
            knowledge_root=KNOWLEDGE_ROOT,
        )

    except (KnowledgeLoadError, KnowledgeValidationError) as exc:
        print()
        print("Knowledge validation FAILED")
        print(f"Reason: {exc}")
        raise SystemExit(1) from exc

    print()
    print("Knowledge validation PASSED")
    print(f"Documents: {len(documents)}")

    for document in documents:
        print(
            f"  - {document.id} "
            f"[{document.category}/{document.topic}] "
            f"v{document.version}"
        )


if __name__ == "__main__":
    main()