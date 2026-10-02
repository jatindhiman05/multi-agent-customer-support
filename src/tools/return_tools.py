from __future__ import annotations

import uuid

from langchain_core.tools import tool

from src.db.session import SessionLocal
from src.repositories.order_repository import OrderRepository
from src.repositories.return_repository import ReturnRepository
from src.services.return_service import (
    OrderNotFoundError,
    ReturnService,
)


def _parse_customer_id(customer_id: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(customer_id)
    except (ValueError, TypeError):
        return None


@tool
def get_returnable_order_items(
    order_number: str,
    customer_id: str,
) -> dict:
    """
    Get the items in one of the authenticated customer's orders.

    Use this before checking return eligibility when the customer
    identifies an order but not the internal order item ID.
    """

    customer_uuid = _parse_customer_id(customer_id)

    if customer_uuid is None:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    with SessionLocal() as session:
        repository = OrderRepository(session)

        order = repository.get_with_details(
            order_number=order_number,
            user_id=customer_uuid,
        )

        if order is None:
            return {
                "success": False,
                "error": "order_not_found",
            }

        return {
            "success": True,
            "order_number": order.order_number,
            "order_status": order.status,
            "items": [
                {
                    "order_item_id": str(item.id),
                    "sku": item.sku,
                    "product_name": item.product_name,
                    "purchased_quantity": item.quantity,
                }
                for item in order.items
            ],
        }


@tool
def check_return_eligibility(
    order_number: str,
    order_item_id: str,
    quantity: int,
    customer_id: str,
) -> dict:
    """
    Check whether a quantity of a specific order item can be returned.
    """

    customer_uuid = _parse_customer_id(customer_id)

    if customer_uuid is None:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    try:
        item_uuid = uuid.UUID(order_item_id)
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": "invalid_order_item_id",
        }

    with SessionLocal() as session:
        service = ReturnService(session)

        try:
            result = service.check_return_eligibility(
                order_number=order_number,
                customer_id=customer_uuid,
                order_item_id=item_uuid,
                quantity=quantity,
            )
        except OrderNotFoundError:
            return {
                "success": False,
                "error": "order_not_found",
            }

        return {
            "success": True,
            "allowed": result.allowed,
            "reason": result.reason,
            "purchased_quantity": result.purchased_quantity,
            "consumed_quantity": result.consumed_quantity,
            "returnable_quantity": result.returnable_quantity,
        }


@tool
def get_return_status(
    return_number: str,
    customer_id: str,
) -> dict:
    """
    Get an existing return belonging to the authenticated customer.
    """

    customer_uuid = _parse_customer_id(customer_id)

    if customer_uuid is None:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    with SessionLocal() as session:
        repository = ReturnRepository(session)

        result = repository.get_with_details(
            return_number=return_number,
            user_id=customer_uuid,
        )

        if result is None:
            return {
                "success": False,
                "error": "return_not_found",
            }

        return {
            "success": True,
            "return_number": result.return_number,
            "status": result.status,
            "reason": result.reason,
            "requested_at": result.requested_at.isoformat(),
            "received_at": (
                result.received_at.isoformat()
                if result.received_at
                else None
            ),
            "completed_at": (
                result.completed_at.isoformat()
                if result.completed_at
                else None
            ),
            "items": [
                {
                    "order_item_id": str(item.order_item_id),
                    "quantity": item.quantity,
                }
                for item in result.items
            ],
        }