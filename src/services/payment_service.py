from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from src.repositories.order_repository import OrderRepository
from src.repositories.payment_repository import PaymentRepository
from src.repositories.refund_repository import RefundRepository


class OrderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class PaymentInfo:
    payment_id: uuid.UUID
    status: str
    amount: Decimal
    currency: str
    payment_method: str
    provider: str
    failure_code: str | None
    failure_message: str | None


@dataclass(frozen=True)
class RefundInfo:
    refund_id: uuid.UUID
    status: str
    amount: Decimal
    currency: str
    reason: str | None
    failure_code: str | None
    failure_message: str | None


@dataclass(frozen=True)
class OrderPaymentSummary:
    order_number: str
    order_status: str
    payments: list[PaymentInfo]
    refunds: list[RefundInfo]


class PaymentService:
    def __init__(self, session: Session):
        self.orders = OrderRepository(session)
        self.payments = PaymentRepository(session)
        self.refunds = RefundRepository(session)

    def get_order_payment_summary(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
    ) -> OrderPaymentSummary:
        # Ownership check happens here.
        order = self.orders.get_for_customer(
            order_number=order_number,
            user_id=customer_id,
        )

        if order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        payments = self.payments.list_for_order(
            order.id
        )

        payment_infos: list[PaymentInfo] = []
        refund_infos: list[RefundInfo] = []

        for payment in payments:
            payment_infos.append(
                PaymentInfo(
                    payment_id=payment.id,
                    status=payment.status,
                    amount=payment.amount,
                    currency=payment.currency,
                    payment_method=payment.payment_method,
                    provider=payment.provider,
                    failure_code=payment.failure_code,
                    failure_message=payment.failure_message,
                )
            )

            refunds = self.refunds.list_for_payment(
                payment.id
            )

            for refund in refunds:
                refund_infos.append(
                    RefundInfo(
                        refund_id=refund.id,
                        status=refund.status,
                        amount=refund.amount,
                        currency=refund.currency,
                        reason=refund.reason,
                        failure_code=refund.failure_code,
                        failure_message=refund.failure_message,
                    )
                )

        return OrderPaymentSummary(
            order_number=order.order_number,
            order_status=order.status,
            payments=payment_infos,
            refunds=refund_infos,
        )