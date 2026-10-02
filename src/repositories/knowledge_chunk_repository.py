from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

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