from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from src.knowledge.schema import KnowledgeDocument


class KnowledgeValidationError(ValueError):
    """Raised when the knowledge collection violates repository rules."""


def validate_knowledge_collection(
    documents: list[KnowledgeDocument],
    *,
    knowledge_root: str | Path,
) -> None:
    """
    Validate rules that apply across the complete knowledge collection.
    """

    if not documents:
        raise KnowledgeValidationError(
            "Knowledge base contains no documents."
        )

    root = Path(knowledge_root).resolve()

    ids = [document.id for document in documents]

    duplicate_ids = sorted(
        document_id
        for document_id, count in Counter(ids).items()
        if count > 1
    )

    if duplicate_ids:
        raise KnowledgeValidationError(
            "Duplicate knowledge document IDs: "
            + ", ".join(duplicate_ids)
        )

    for document in documents:
        source = document.source_path.resolve()

        try:
            relative_source = source.relative_to(root)
        except ValueError as exc:
            raise KnowledgeValidationError(
                f"{document.id}: source is outside the knowledge directory."
            ) from exc

        if not relative_source.parts:
            raise KnowledgeValidationError(
                f"{document.id}: invalid source path."
            )

        directory_category = relative_source.parts[0]

        if directory_category != document.category:
            raise KnowledgeValidationError(
                f"{document.id}: category '{document.category}' "
                f"does not match directory '{directory_category}'."
            )

        if document.last_reviewed < document.effective_date:
            raise KnowledgeValidationError(
                f"{document.id}: last_reviewed cannot be before "
                "effective_date."
            )

        if document.effective_date > date.today():
            raise KnowledgeValidationError(
                f"{document.id}: effective_date cannot be in the future."
            )