from __future__ import annotations

import uuid

from langchain_core.tools import tool

from src.db.session import SessionLocal
from src.services.shipment_service import OrderNotFoundError, ShipmentService


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
        except OrderNotFoundError:
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