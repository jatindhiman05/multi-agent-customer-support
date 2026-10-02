from __future__ import annotations

import uuid

from langchain_core.tools import tool
from src.db.session import SessionLocal
from src.services.order_service import (
    OrderNotFoundError as OrderServiceNotFoundError,
    OrderService,
)
from src.services.shipment_service import (
    OrderNotFoundError as ShipmentOrderNotFoundError,
    ShipmentService,
)


@tool
def list_customer_orders(
    customer_id: str,
) -> dict:
    """List orders belonging to the authenticated customer."""

    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    with SessionLocal() as session:
        service = OrderService(session)

        orders = service.list_customer_orders(
            customer_id=customer_uuid,
        )

        return {
            "success": True,
            "orders": [
                {
                    "order_number": order.order_number,
                    "status": order.status,
                    "total_amount": str(order.total_amount),
                    "currency": order.currency,
                    "created_at": order.created_at.isoformat(),
                }
                for order in orders
            ],
        }


@tool
def get_order_tracking(
    order_number: str,
    customer_id: str,
) -> dict:
    """
    Get shipment and tracking information for a customer's order.

    Use this tool when the customer asks where their order is,
    whether it has shipped, or for tracking information.

    Args:
        order_number: Public order number, for example ORD-1003.
        customer_id: Authenticated customer's UUID.
    """

    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    with SessionLocal() as session:
        service = ShipmentService(session)

        try:
            result = service.get_order_tracking(
                order_number=order_number,
                customer_id=customer_uuid,
            )
        except ShipmentOrderNotFoundError:
            return {
                "success": False,
                "error": "order_not_found",
            }

        return {
            "success": True,
            "order_number": result.order_number,
            "order_status": result.order_status,
            "shipments": [
                {
                    "tracking_number": shipment.tracking_number,
                    "carrier": shipment.carrier,
                    "status": shipment.status,
                    "estimated_delivery_at": (
                        shipment.estimated_delivery_at.isoformat()
                        if shipment.estimated_delivery_at
                        else None
                    ),
                    "delivered_at": (
                        shipment.delivered_at.isoformat()
                        if shipment.delivered_at
                        else None
                    ),
                    "events": [
                        {
                            "status": event.status,
                            "description": event.description,
                            "location": event.location,
                            "occurred_at": event.occurred_at.isoformat(),
                        }
                        for event in shipment.events
                    ],
                }
                for shipment in result.shipments
            ],
        }


@tool
def get_customer_order(
    order_number: str,
    customer_id: str,
) -> dict:
    """
    Get detailed information about one of the authenticated
    customer's orders, including purchased items and payment status.

    Use this when information about the order itself or the products
    purchased in the order is required.
    """

    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    with SessionLocal() as session:
        service = OrderService(session)

        try:
            order = service.get_order(
                order_number=order_number,
                customer_id=customer_uuid,
            )
        except OrderServiceNotFoundError:
            return {
                "success": False,
                "error": "order_not_found",
            }

        return {
            "success": True,
            "order_number": order.order_number,
            "status": order.status,
            "currency": order.currency,
            "subtotal": str(order.subtotal),
            "shipping_amount": str(order.shipping_amount),
            "tax_amount": str(order.tax_amount),
            "discount_amount": str(order.discount_amount),
            "total_amount": str(order.total_amount),
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "sku": item.sku,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "line_total": str(item.line_total),
                }
                for item in order.items
            ],
            "payments": [
                {
                    "payment_method": payment.payment_method,
                    "status": payment.status,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                }
                for payment in order.payments
            ],
        }