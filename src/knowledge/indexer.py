from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from sqlalchemy.orm import Session

from src.db.models import KnowledgeChunkRecord
from src.knowledge.embeddings import EmbeddingProvider
from src.knowledge.schema import KnowledgeChunk
from src.repositories.knowledge_chunk_repository import (
    KnowledgeChunkRepository,
)


@dataclass(frozen=True)
class KnowledgeIndexStats:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    embedded: int = 0


class KnowledgeIndexer:
    """
    Synchronize authoritative knowledge chunks into PostgreSQL.

    Markdown remains the source of truth. The knowledge_chunks table is
    a rebuildable semantic-search index.

    The caller owns the database transaction.
    """

    def __init__(
        self,
        session: Session,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.session = session
        self.embedding_provider = embedding_provider
        self.repository = KnowledgeChunkRepository(session)

    def sync(
        self,
        chunks: list[KnowledgeChunk],
    ) -> KnowledgeIndexStats:
        self._validate_embedding_dimension()

        self._validate_unique_chunk_ids(chunks)

        existing_records = {
            record.id: record
            for record in self.repository.list_all()
        }

        incoming_ids = {
            chunk.id
            for chunk in chunks
        }

        existing_ids = set(existing_records)

        stale_ids = existing_ids - incoming_ids

        new_chunks: list[KnowledgeChunk] = []
        reembed_chunks: list[KnowledgeChunk] = []
        metadata_only_chunks: list[KnowledgeChunk] = []
        unchanged_chunks: list[KnowledgeChunk] = []

        for chunk in chunks:
            existing = existing_records.get(chunk.id)

            if existing is None:
                new_chunks.append(chunk)
                continue

            if self._requires_reembedding(
                chunk=chunk,
                existing=existing,
            ):
                reembed_chunks.append(chunk)
                continue

            if self._requires_metadata_update(
                chunk=chunk,
                existing=existing,
            ):
                metadata_only_chunks.append(chunk)
                continue

            unchanged_chunks.append(chunk)

        chunks_to_embed = [
            *new_chunks,
            *reembed_chunks,
        ]

        embeddings = self._embed_chunks(
            chunks_to_embed
        )

        embedding_by_id = {
            chunk.id: embedding
            for chunk, embedding in zip(
                chunks_to_embed,
                embeddings,
                strict=True,
            )
        }

        now = datetime.now(timezone.utc)

        for chunk in new_chunks:
            record = self._create_record(
                chunk=chunk,
                embedding=embedding_by_id[chunk.id],
                now=now,
            )

            self.repository.add(record)

        for chunk in reembed_chunks:
            record = existing_records[chunk.id]

            self._update_record(
                record=record,
                chunk=chunk,
                embedding=embedding_by_id[chunk.id],
                now=now,
            )

        for chunk in metadata_only_chunks:
            record = existing_records[chunk.id]

            self._update_record(
                record=record,
                chunk=chunk,
                embedding=None,
                now=now,
            )

        deleted = self.repository.delete_by_ids(
            stale_ids
        )

        self.repository.flush()

        return KnowledgeIndexStats(
            inserted=len(new_chunks),
            updated=(
                len(reembed_chunks)
                + len(metadata_only_chunks)
            ),
            unchanged=len(unchanged_chunks),
            deleted=deleted,
            embedded=len(chunks_to_embed),
        )

    def _validate_embedding_dimension(self) -> None:
        expected_dimension = 384

        if self.embedding_provider.dimension != expected_dimension:
            raise ValueError(
                "Knowledge embedding dimension mismatch: "
                f"database expects {expected_dimension}, "
                f"but model "
                f"'{self.embedding_provider.model_name}' "
                f"produces "
                f"{self.embedding_provider.dimension}."
            )

    @staticmethod
    def _validate_unique_chunk_ids(
        chunks: list[KnowledgeChunk],
    ) -> None:
        seen: set[str] = set()

        for chunk in chunks:
            if chunk.id in seen:
                raise ValueError(
                    f"Duplicate knowledge chunk ID: "
                    f"{chunk.id}"
                )

            seen.add(chunk.id)

    def _requires_reembedding(
        self,
        chunk: KnowledgeChunk,
        existing: KnowledgeChunkRecord,
    ) -> bool:
        return (
            existing.embedding_hash
            != chunk.embedding_hash
            or existing.embedding_model
            != self.embedding_provider.model_name
        )

    @staticmethod
    def _requires_metadata_update(
        chunk: KnowledgeChunk,
        existing: KnowledgeChunkRecord,
    ) -> bool:
        return any(
            (
                existing.document_id != chunk.document_id,
                existing.chunk_index != chunk.chunk_index,
                existing.title != chunk.title,
                existing.heading != chunk.heading,
                existing.category != chunk.category,
                existing.topic != chunk.topic,
                existing.version != chunk.version,
                existing.status != chunk.status,
                existing.effective_date != chunk.effective_date,
                existing.last_reviewed != chunk.last_reviewed,
                existing.owner != chunk.owner,
                existing.content != chunk.content,
                existing.embedding_text != chunk.embedding_text,
                existing.content_hash != chunk.content_hash,
                existing.embedding_hash != chunk.embedding_hash,
                existing.source_path
                != chunk.source_path.as_posix(),
            )
        )

    def _embed_chunks(
        self,
        chunks: list[KnowledgeChunk],
    ) -> np.ndarray:
        if not chunks:
            return np.empty(
                (
                    0,
                    self.embedding_provider.dimension,
                ),
                dtype=np.float32,
            )

        embeddings = (
            self.embedding_provider.embed_documents(
                [
                    chunk.embedding_text
                    for chunk in chunks
                ]
            )
        )

        expected_shape = (
            len(chunks),
            self.embedding_provider.dimension,
        )

        if embeddings.shape != expected_shape:
            raise ValueError(
                "Unexpected embedding matrix shape: "
                f"expected {expected_shape}, "
                f"received {embeddings.shape}."
            )

        return embeddings

    def _create_record(
        self,
        chunk: KnowledgeChunk,
        embedding: np.ndarray,
        now: datetime,
    ) -> KnowledgeChunkRecord:
        return KnowledgeChunkRecord(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            title=chunk.title,
            heading=chunk.heading,
            category=chunk.category,
            topic=chunk.topic,
            version=chunk.version,
            status=chunk.status,
            effective_date=chunk.effective_date,
            last_reviewed=chunk.last_reviewed,
            owner=chunk.owner,
            content=chunk.content,
            embedding_text=chunk.embedding_text,
            content_hash=chunk.content_hash,
            embedding_hash=chunk.embedding_hash,
            source_path=chunk.source_path.as_posix(),
            embedding=embedding.tolist(),
            embedding_model=(
                self.embedding_provider.model_name
            ),
            created_at=now,
            updated_at=now,
        )

    def _update_record(
        self,
        record: KnowledgeChunkRecord,
        chunk: KnowledgeChunk,
        embedding: np.ndarray | None,
        now: datetime,
    ) -> None:
        record.document_id = chunk.document_id
        record.chunk_index = chunk.chunk_index

        record.title = chunk.title
        record.heading = chunk.heading

        record.category = chunk.category
        record.topic = chunk.topic

        record.version = chunk.version
        record.status = chunk.status

        record.effective_date = chunk.effective_date
        record.last_reviewed = chunk.last_reviewed

        record.owner = chunk.owner

        record.content = chunk.content
        record.embedding_text = chunk.embedding_text

        record.content_hash = chunk.content_hash
        record.embedding_hash = chunk.embedding_hash

        record.source_path = (
            chunk.source_path.as_posix()
        )

        if embedding is not None:
            record.embedding = embedding.tolist()
            record.embedding_model = (
                self.embedding_provider.model_name
            )

        record.updated_at = now