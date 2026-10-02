from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import IdempotencyRecord


class IdempotencyRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def get(
        self,
        *,
        user_id: uuid.UUID,
        action_id: str,
    ) -> IdempotencyRecord | None:
        statement = (
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id
                == user_id,
                IdempotencyRecord.action_id
                == action_id,
            )
        )

        return self.session.scalar(
            statement
        )

    def get_for_update(
        self,
        *,
        user_id: uuid.UUID,
        action_id: str,
    ) -> IdempotencyRecord | None:
        statement = (
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id
                == user_id,
                IdempotencyRecord.action_id
                == action_id,
            )
            .with_for_update()
        )

        return self.session.scalar(
            statement
        )

    def add(
        self,
        record: IdempotencyRecord,
    ) -> IdempotencyRecord:
        self.session.add(record)
        self.session.flush()

        return record