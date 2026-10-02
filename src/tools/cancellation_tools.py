from __future__ import annotations

import uuid

from langchain_core.tools import tool

from src.db.session import SessionLocal
from src.services.order_service import (
    OrderNotFoundError,
    OrderService,
)


def _parse_customer_id(
    customer_id: str,
) -> uuid.UUID:
    try:
        return uuid.UUID(customer_id)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            "Invalid trusted customer ID."
        ) from exc


@tool
def check_order_cancellation(
    order_number: str,
    customer_id: str,
) -> dict:
    """
    Check whether an authenticated customer's order can currently
    be cancelled.

    This tool performs no mutation.
    """

    try:
        customer_uuid = _parse_customer_id(
            customer_id
        )
    except ValueError:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    with SessionLocal() as session:
        service = OrderService(session)

        try:
            eligibility = (
                service.check_cancellation_eligibility(
                    order_number=order_number,
                    customer_id=customer_uuid,
                )
            )

            return {
                "success": True,
                "order_number": order_number,
                "allowed": eligibility.allowed,
                "reason": eligibility.reason,
            }

        except OrderNotFoundError:
            return {
                "success": False,
                "error": "order_not_found",
            }