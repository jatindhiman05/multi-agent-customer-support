from __future__ import annotations

import uuid

from sqlalchemy.orm import Session
from dataclasses import dataclass
from src.db.models import Order
from src.repositories.order_repository import OrderRepository


class OrderNotFoundError(Exception):
    pass

@dataclass(frozen=True)
class CancellationEligibility:
    allowed: bool
    reason: str

class OrderService:
    CANCELLABLE_STATUSES = {
        "pending",
        "confirmed",
        "processing",
    }

    def __init__(self, session: Session):
        self.session = session
        self.orders = OrderRepository(session)

    def get_order(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
    ) -> Order:
        order = self.orders.get_with_details(
            order_number=order_number,
            user_id=customer_id,
        )

        if order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        return order

    def check_cancellation_eligibility(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
    ) -> CancellationEligibility:
        order = self.get_order(
            order_number=order_number,
            customer_id=customer_id,
        )

        if order.status in self.CANCELLABLE_STATUSES:
            return CancellationEligibility(
                allowed=True,
                reason="eligible",
            )

        if order.status == "shipped":
            return CancellationEligibility(
                allowed=False,
                reason="already_shipped",
            )

        if order.status == "delivered":
            return CancellationEligibility(
                allowed=False,
                reason="already_delivered",
            )

        if order.status == "cancelled":
            return CancellationEligibility(
                allowed=False,
                reason="already_cancelled",
            )

        return CancellationEligibility(
            allowed=False,
            reason="status_not_cancellable",
        )