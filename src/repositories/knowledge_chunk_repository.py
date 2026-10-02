from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from src.knowledge.schema import (
    KnowledgeChunk,
    KnowledgeSearchResult,
)
from src.db.models import KnowledgeChunkRecord


class KnowledgeChunkRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[KnowledgeChunkRecord]:
        statement = select(KnowledgeChunkRecord)

        return list(
            self.session.scalars(statement).all()
        )

    def get_by_id(
        self,
        chunk_id: str,
    ) -> KnowledgeChunkRecord | None:
        statement = (
            select(KnowledgeChunkRecord)
            .where(KnowledgeChunkRecord.id == chunk_id)
        )

        return self.session.scalar(statement)

    def add(
        self,
        record: KnowledgeChunkRecord,
    ) -> None:
        self.session.add(record)

    def delete_by_ids(
        self,
        chunk_ids: set[str],
    ) -> int:
        if not chunk_ids:
            return 0

        statement = (
            delete(KnowledgeChunkRecord)
            .where(KnowledgeChunkRecord.id.in_(chunk_ids))
        )

        result = self.session.execute(statement)

        return result.rowcount or 0

    def flush(self) -> None:
        self.session.flush()

    def search_by_embedding(
        self,
        query_embedding: list[float],
        *,
        embedding_model: str,
        top_k: int,
    ) -> list[KnowledgeSearchResult]:
        distance = (
            KnowledgeChunkRecord.embedding.cosine_distance(
                query_embedding
            )
        )

        statement = (
            select(
                KnowledgeChunkRecord,
                distance.label("distance"),
            )
            .where(
                KnowledgeChunkRecord.status == "published",
                KnowledgeChunkRecord.embedding_model
                == embedding_model,
            )
            .order_by(distance)
            .limit(top_k)
        )

        rows = self.session.execute(statement).all()

        results: list[KnowledgeSearchResult] = []

        for record, cosine_distance in rows:
            chunk = KnowledgeChunk(
                id=record.id,
                document_id=record.document_id,
                chunk_index=record.chunk_index,
                title=record.title,
                heading=record.heading,
                category=record.category,
                topic=record.topic,
                version=record.version,
                status=record.status,
                effective_date=record.effective_date,
                last_reviewed=record.last_reviewed,
                owner=record.owner,
                content=record.content,
                embedding_text=record.embedding_text,
                content_hash=record.content_hash,
                embedding_hash=record.embedding_hash,
                source_path=record.source_path,
            )

            results.append(
                KnowledgeSearchResult(
                    chunk=chunk,
                    score=1.0 - float(cosine_distance),
                )
            )

        return results