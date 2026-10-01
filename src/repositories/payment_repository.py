from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Payment


class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(
        self,
        payment_id: uuid.UUID,
    ) -> Payment | None:
        statement = (
            select(Payment)
            .where(Payment.id == payment_id)
        )

        return self.session.scalar(statement)

    def list_for_order(
        self,
        order_id: uuid.UUID,
    ) -> list[Payment]:
        statement = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.asc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_latest_captured_for_order(
        self,
        order_id: uuid.UUID,
    ) -> Payment | None:
        statement = (
            select(Payment)
            .where(
                Payment.order_id == order_id,
                Payment.status.in_(
                    {
                        "captured",
                        "partially_refunded",
                    }
                ),
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )

        return self.session.scalar(statement)

    def set_status(
        self,
        payment: Payment,
        status: str,
    ) -> None:
        payment.status = status
        self.session.flush()

    def get_by_id_for_update(
        self,
        payment_id: uuid.UUID,
    ) -> Payment | None:
        statement = (
            select(Payment)
            .where(Payment.id == payment_id)
            .with_for_update()
        )

        return self.session.scalar(statement)