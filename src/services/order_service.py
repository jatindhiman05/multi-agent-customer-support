from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.db.models import Order
from src.repositories.order_repository import OrderRepository


class OrderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class CancellationEligibility:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class CancellationResult:
    cancelled: bool
    reason: str
    requires_refund: bool


class OrderService:
    CANCELLABLE_STATUSES = {
        "pending",
        "confirmed",
        "processing",
    }

    BLOCKING_SHIPMENT_STATUSES = {
        "shipped",
        "in_transit",
        "out_for_delivery",
        "delivered",
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

        # ---------------------------------------------------------
        # ORDER-LEVEL CHECKS
        # ---------------------------------------------------------

        if order.status == "cancelled":
            return CancellationEligibility(
                allowed=False,
                reason="already_cancelled",
            )

        if order.status == "delivered":
            return CancellationEligibility(
                allowed=False,
                reason="already_delivered",
            )

        if order.status == "shipped":
            return CancellationEligibility(
                allowed=False,
                reason="already_shipped",
            )

        # ---------------------------------------------------------
        # FULFILLMENT CHECKS
        # ---------------------------------------------------------

        # Even if the order status has not yet been updated,
        # an actual dispatched shipment blocks cancellation.
        for shipment in order.shipments:
            if shipment.status in self.BLOCKING_SHIPMENT_STATUSES:
                return CancellationEligibility(
                    allowed=False,
                    reason="shipment_already_dispatched",
                )

        # ---------------------------------------------------------
        # STATUS POLICY
        # ---------------------------------------------------------

        if order.status not in self.CANCELLABLE_STATUSES:
            return CancellationEligibility(
                allowed=False,
                reason="status_not_cancellable",
            )

        return CancellationEligibility(
            allowed=True,
            reason="eligible",
        )

    def cancel_order(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
    ) -> CancellationResult:
        # ---------------------------------------------------------
        # LOAD CUSTOMER-OWNED ORDER
        # ---------------------------------------------------------

        order = self.get_order(
            order_number=order_number,
            customer_id=customer_id,
        )

        # ---------------------------------------------------------
        # RE-CHECK BUSINESS ELIGIBILITY
        # ---------------------------------------------------------

        eligibility = self.check_cancellation_eligibility(
            order_number=order_number,
            customer_id=customer_id,
        )

        if not eligibility.allowed:
            return CancellationResult(
                cancelled=False,
                reason=eligibility.reason,
                requires_refund=False,
            )

        # ---------------------------------------------------------
        # PAYMENT CHECK
        # ---------------------------------------------------------

        captured_payment_exists = any(
            payment.status in {
                "captured",
                "partially_refunded",
            }
            for payment in order.payments
        )

        # We deliberately do not pretend a captured payment
        # has been refunded. That requires a separate refund
        # workflow.
        if captured_payment_exists:
            return CancellationResult(
                cancelled=False,
                reason="captured_payment_requires_refund",
                requires_refund=True,
            )

        # ---------------------------------------------------------
        # MUTATION
        # ---------------------------------------------------------

        self.orders.set_status(
            order=order,
            status="cancelled",
        )

        return CancellationResult(
            cancelled=True,
            reason="cancelled",
            requires_refund=False,
        )