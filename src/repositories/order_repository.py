from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.db.models import Order


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(
        self,
        order_id: uuid.UUID,
    ) -> Order | None:
        statement = (
            select(Order)
            .where(Order.id == order_id)
        )

        return self.session.scalar(statement)

    def get_by_number(
        self,
        order_number: str,
    ) -> Order | None:
        statement = (
            select(Order)
            .where(Order.order_number == order_number)
        )

        return self.session.scalar(statement)

    def get_for_customer(
        self,
        order_number: str,
        user_id: uuid.UUID,
    ) -> Order | None:
        statement = (
            select(Order)
            .where(
                Order.order_number == order_number,
                Order.user_id == user_id,
            )
        )

        return self.session.scalar(statement)

    def list_for_customer(
        self,
        user_id: uuid.UUID,
    ) -> list[Order]:
        statement = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_with_details(
        self,
        order_number: str,
        user_id: uuid.UUID,
    ) -> Order | None:
        statement = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payments),
                selectinload(Order.shipments),
                selectinload(Order.returns),
            )
            .where(
                Order.order_number == order_number,
                Order.user_id == user_id,
            )
        )

        return self.session.scalar(statement)

    def set_status(
        self,
        order: Order,
        status: str,
    ) -> None:
        order.status = status

        # Send the UPDATE to PostgreSQL, but do NOT commit.
        # The service/caller owns the transaction boundary.
        self.session.flush()