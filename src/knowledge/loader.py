from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.knowledge.schema import KnowledgeDocument


class KnowledgeLoadError(ValueError):
    """Raised when a knowledge source file cannot be parsed."""


def _parse_frontmatter(text: str, source_path: Path) -> tuple[dict[str, Any], str]:
    """
    Split a Markdown document into YAML frontmatter and Markdown content.
    """

    if not text.startswith("---"):
        raise KnowledgeLoadError(
            f"{source_path}: missing YAML frontmatter."
        )

    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        raise KnowledgeLoadError(
            f"{source_path}: frontmatter must begin with '---'."
        )

    closing_index: int | None = None

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise KnowledgeLoadError(
            f"{source_path}: frontmatter is missing its closing '---'."
        )

    raw_frontmatter = "\n".join(lines[1:closing_index])

    try:
        metadata = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:
        raise KnowledgeLoadError(
            f"{source_path}: invalid YAML frontmatter."
        ) from exc

    if not isinstance(metadata, dict):
        raise KnowledgeLoadError(
            f"{source_path}: frontmatter must contain a YAML mapping."
        )

    content = "\n".join(lines[closing_index + 1:]).strip()

    if not content:
        raise KnowledgeLoadError(
            f"{source_path}: document content is empty."
        )

    return metadata, content


def load_knowledge_document(path: str | Path) -> KnowledgeDocument:
    """
    Load and validate one Markdown knowledge document.
    """

    source_path = Path(path)

    if not source_path.exists():
        raise KnowledgeLoadError(
            f"{source_path}: file does not exist."
        )

    if not source_path.is_file():
        raise KnowledgeLoadError(
            f"{source_path}: expected a file."
        )

    if source_path.suffix.lower() != ".md":
        raise KnowledgeLoadError(
            f"{source_path}: knowledge documents must be Markdown files."
        )

    try:
        text = source_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise KnowledgeLoadError(
            f"{source_path}: file must be valid UTF-8."
        ) from exc

    metadata, content = _parse_frontmatter(
        text=text,
        source_path=source_path,
    )

    try:
        return KnowledgeDocument(
            **metadata,
            content=content,
            source_path=source_path,
        )
    except Exception as exc:
        raise KnowledgeLoadError(
            f"{source_path}: invalid knowledge document: {exc}"
        ) from exc


def load_knowledge_directory(
    root: str | Path,
) -> list[KnowledgeDocument]:
    """
    Recursively load every Markdown knowledge document below root.
    """

    root_path = Path(root)

    if not root_path.exists():
        raise KnowledgeLoadError(
            f"{root_path}: knowledge directory does not exist."
        )

    if not root_path.is_dir():
        raise KnowledgeLoadError(
            f"{root_path}: expected a directory."
        )

    documents: list[KnowledgeDocument] = []

    for path in sorted(root_path.rglob("*.md")):
        documents.append(load_knowledge_document(path))

    return documents