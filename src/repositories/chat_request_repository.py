from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.db.models import ChatRequestRecord


class ChatRequestRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def get(
        self,
        *,
        customer_id: uuid.UUID,
        request_id: uuid.UUID,
    ) -> ChatRequestRecord | None:
        statement = select(
            ChatRequestRecord
        ).where(
            ChatRequestRecord.customer_id
            == customer_id,
            ChatRequestRecord.request_id
            == request_id,
        )

        return self.session.scalar(statement)

    def add(
        self,
        record: ChatRequestRecord,
    ) -> ChatRequestRecord:
        self.session.add(record)
        self.session.flush()

        return record

    def delete(
        self,
        *,
        customer_id: uuid.UUID,
        request_id: uuid.UUID,
    ) -> None:
        statement = delete(
            ChatRequestRecord
        ).where(
            ChatRequestRecord.customer_id
            == customer_id,
            ChatRequestRecord.request_id
            == request_id,
        )

        self.session.execute(statement)