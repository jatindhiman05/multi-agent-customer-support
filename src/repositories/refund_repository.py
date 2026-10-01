from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Refund


class RefundRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(
        self,
        refund_id: uuid.UUID,
    ) -> Refund | None:
        statement = (
            select(Refund)
            .where(Refund.id == refund_id)
        )

        return self.session.scalar(statement)

    def list_for_payment(
        self,
        payment_id: uuid.UUID,
    ) -> list[Refund]:
        statement = (
            select(Refund)
            .where(Refund.payment_id == payment_id)
            .order_by(Refund.created_at.asc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_by_provider_refund_id(
        self,
        provider: str,
        provider_refund_id: str,
    ) -> Refund | None:
        statement = (
            select(Refund)
            .where(
                Refund.provider == provider,
                Refund.provider_refund_id == provider_refund_id,
            )
        )

        return self.session.scalar(statement)

    def add(
        self,
        refund: Refund,
    ) -> Refund:
        self.session.add(refund)
        self.session.flush()

        return refund

    def set_status(
        self,
        refund: Refund,
        status: str,
    ) -> None:
        refund.status = status
        self.session.flush()