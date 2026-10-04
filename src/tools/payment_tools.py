from __future__ import annotations

import uuid

from langchain_core.tools import tool

from src.db.session import SessionLocal
from src.services.payment_service import (
    OrderNotFoundError,
    PaymentService,
)


def _parse_customer_id(
    customer_id: str,
) -> uuid.UUID | None:
    try:
        return uuid.UUID(customer_id)
    except (ValueError, TypeError):
        return None


@tool
def get_order_payment_status(
    order_number: str,
    customer_id: str,
) -> dict:
    """
    Get payment and refund information for one of the
    authenticated customer's orders.

    Use this for questions about payment status, failed
    payments, charged amounts, payment methods, duplicate
    charges, and refund status.
    """

    customer_uuid = _parse_customer_id(
        customer_id
    )

    if customer_uuid is None:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    with SessionLocal() as session:
        service = PaymentService(session)

        try:
            result = (
                service.get_order_payment_summary(
                    order_number=order_number,
                    customer_id=customer_uuid,
                )
            )
        except OrderNotFoundError:
            return {
                "success": False,
                "error": "order_not_found",
            }

        return {
            "success": True,
            "order_number": result.order_number,
            "order_status": result.order_status,
            "payments": [
                {
                    "payment_id": str(
                        payment.payment_id
                    ),
                    "status": payment.status,
                    "amount": str(
                        payment.amount
                    ),
                    "currency": (
                        payment.currency
                    ),
                    "payment_method": (
                        payment.payment_method
                    ),
                    "provider": (
                        payment.provider
                    ),
                    "failure_code": (
                        payment.failure_code
                    ),
                    "failure_message": (
                        payment.failure_message
                    ),
                }
                for payment in result.payments
            ],
            "refunds": [
                {
                    "refund_id": str(
                        refund.refund_id
                    ),
                    "status": refund.status,
                    "amount": str(
                        refund.amount
                    ),
                    "currency": (
                        refund.currency
                    ),
                    "reason": refund.reason,
                    "failure_code": (
                        refund.failure_code
                    ),
                    "failure_message": (
                        refund.failure_message
                    ),
                }
                for refund in result.refunds
            ],
        }