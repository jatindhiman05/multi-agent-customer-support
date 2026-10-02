from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.db.models import Order
from src.repositories.order_repository import OrderRepository
from src.services.refund_service import RefundService


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
    refund_id: uuid.UUID | None = None


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
        self.refunds = RefundService(session)

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

    def list_customer_orders(
        self,
        *,
        customer_id: uuid.UUID,
    ) -> list[Order]:
        """
        Return all orders belonging to the authenticated customer,
        newest first.
        """

        return self.orders.list_for_customer(
            user_id=customer_id,
        )

    def _check_order_cancellation_eligibility(
        self,
        order: Order,
    ) -> CancellationEligibility:
        """
        Apply cancellation rules to an already-loaded order.

        This helper allows the same business rules to be reused by both
        the read-only eligibility path and the locked mutation path.
        """

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

        # Even if order.status has not yet been updated, an actual
        # dispatched shipment blocks cancellation.
        for shipment in order.shipments:
            if shipment.status in self.BLOCKING_SHIPMENT_STATUSES:
                return CancellationEligibility(
                    allowed=False,
                    reason="shipment_already_dispatched",
                )

        if order.status not in self.CANCELLABLE_STATUSES:
            return CancellationEligibility(
                allowed=False,
                reason="status_not_cancellable",
            )

        return CancellationEligibility(
            allowed=True,
            reason="eligible",
        )

    def check_cancellation_eligibility(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
    ) -> CancellationEligibility:
        """
        Read-only cancellation eligibility check.
        """

        order = self.get_order(
            order_number=order_number,
            customer_id=customer_id,
        )

        return self._check_order_cancellation_eligibility(
            order
        )

    def cancel_order(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
    ) -> CancellationResult:
        """
        Cancel an order while holding an order-level row lock.

        If a refundable captured payment exists, the full remaining
        refundable balance is refunded inside the same SQLAlchemy
        transaction.

        The caller owns commit/rollback.
        """

        # ---------------------------------------------------------
        # LOCK CUSTOMER-OWNED ORDER
        # ---------------------------------------------------------

        order = self.orders.get_for_customer_for_update(
            order_number=order_number,
            user_id=customer_id,
        )

        if order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        # ---------------------------------------------------------
        # RE-CHECK BUSINESS ELIGIBILITY WHILE LOCKED
        # ---------------------------------------------------------

        eligibility = self._check_order_cancellation_eligibility(
            order
        )

        if not eligibility.allowed:
            return CancellationResult(
                cancelled=False,
                reason=eligibility.reason,
                requires_refund=False,
            )

        # ---------------------------------------------------------
        # FIND REFUNDABLE PAYMENTS
        # ---------------------------------------------------------

        refundable_payments = [
            payment
            for payment in order.payments
            if payment.status in {
                "captured",
                "partially_refunded",
            }
        ]

        # ---------------------------------------------------------
        # CAPTURED PAYMENT CANCELLATION
        # ---------------------------------------------------------

        if refundable_payments:
            # Multiple captured/refundable payments represent an
            # unusual financial state. Do not choose one arbitrarily.
            if len(refundable_payments) > 1:
                return CancellationResult(
                    cancelled=False,
                    reason=(
                        "multiple_refundable_payments_require_review"
                    ),
                    requires_refund=True,
                )

            payment = refundable_payments[0]

            # The service, not the LLM, determines the refund amount.
            refundable_amount = (
                self.refunds.calculate_refundable_amount(
                    payment
                )
            )

            if refundable_amount <= 0:
                return CancellationResult(
                    cancelled=False,
                    reason="no_refundable_balance",
                    requires_refund=True,
                )

            # RefundService locks the payment row before creating
            # the refund.
            refund_result = self.refunds.create_refund(
                payment_id=payment.id,
                amount=refundable_amount,
                reason="order_cancellation",
            )

            if not refund_result.created:
                return CancellationResult(
                    cancelled=False,
                    reason=refund_result.reason,
                    requires_refund=True,
                )

            self.orders.set_status(
                order=order,
                status="cancelled",
            )

            return CancellationResult(
                cancelled=True,
                reason="cancelled_with_refund",
                requires_refund=True,
                refund_id=refund_result.refund.id,
            )

        # ---------------------------------------------------------
        # CANCELLATION WITHOUT REFUND
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