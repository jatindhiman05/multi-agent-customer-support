from __future__ import annotations

import hashlib
import re

from src.knowledge.schema import (
    KnowledgeChunk,
    KnowledgeDocument,
)


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _content_hash(content: str) -> str:
    """
    Generate a deterministic SHA-256 fingerprint for chunk content.
    """

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def _normalize_identifier(value: str) -> str:
    """
    Convert a heading into a stable identifier component.
    """

    value = value.strip().lower()

    value = re.sub(r"[^a-z0-9]+", "-", value)

    return value.strip("-") or "section"

def _split_markdown_sections(
    content: str,
) -> list[tuple[str, str]]:
    """
    Split Markdown using headings as semantic boundaries.

    Content between the H1 title and the first H2+ heading is preserved
    as an Overview section.
    """

    sections: list[tuple[str, str]] = []

    current_heading = "Overview"
    current_lines: list[str] = []

    for line in content.splitlines():
        match = HEADING_PATTERN.match(line)

        if match:
            level = len(match.group(1))
            heading = match.group(2).strip()

            if level == 1:
                # The H1 is represented separately by document_title.
                continue

            section_content = "\n".join(current_lines).strip()

            if section_content:
                sections.append(
                    (current_heading, section_content)
                )

            current_heading = heading
            current_lines = []
            continue

        current_lines.append(line)

    section_content = "\n".join(current_lines).strip()

    if section_content:
        sections.append(
            (current_heading, section_content)
        )

    return sections

def chunk_knowledge_document(
    document: KnowledgeDocument,
) -> list[KnowledgeChunk]:
    """
    Convert one validated knowledge document into semantic chunks.
    """

    sections = _split_markdown_sections(document.content)

    if not sections:
        # Fallback for a valid document that has no H2+ headings.
        sections = [
            (
                document.title,
                document.content,
            )
        ]

    chunks: list[KnowledgeChunk] = []

    heading_counts: dict[str, int] = {}

    for chunk_index, (heading, section_content) in enumerate(sections):
        heading_slug = _normalize_identifier(heading)

        occurrence = heading_counts.get(heading_slug, 0)
        heading_counts[heading_slug] = occurrence + 1

        if occurrence:
            heading_slug = f"{heading_slug}-{occurrence + 1}"

        # Give the embedding enough document context to understand
        # otherwise ambiguous section text.
        retrieval_content = (
            f"{document.title}\n"
            f"{heading}\n\n"
            f"{section_content}"
        ).strip()

        chunk_id = f"{document.id}:{heading_slug}"

        chunks.append(
            KnowledgeChunk(
                id=chunk_id,
                document_id=document.id,
                chunk_index=chunk_index,
                title=document.title,
                heading=heading,
                category=document.category,
                topic=document.topic,
                version=document.version,
                status=document.status,
                effective_date=document.effective_date,
                last_reviewed=document.last_reviewed,
                owner=document.owner,
                content=retrieval_content,
                content_hash=_content_hash(retrieval_content),
                source_path=document.source_path,
            )
        )

    return chunks


def chunk_knowledge_documents(
    documents: list[KnowledgeDocument],
) -> list[KnowledgeChunk]:
    """
    Chunk a validated collection deterministically.
    """

    chunks: list[KnowledgeChunk] = []

    for document in documents:
        if document.status != "published":
            continue

        chunks.extend(
            chunk_knowledge_document(document)
        )

    return chunks