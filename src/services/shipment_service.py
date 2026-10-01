from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from src.repositories.order_repository import OrderRepository
from src.repositories.shipment_repository import ShipmentRepository


class OrderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class TrackingEventResult:
    status: str
    description: str | None
    location: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class ShipmentTrackingResult:
    tracking_number: str | None
    carrier: str | None
    status: str
    shipped_at: datetime | None
    estimated_delivery_at: datetime | None
    delivered_at: datetime | None
    events: tuple[TrackingEventResult, ...]


@dataclass(frozen=True)
class OrderTrackingResult:
    order_number: str
    order_status: str
    shipments: tuple[ShipmentTrackingResult, ...]


class ShipmentService:
    def __init__(self, session: Session):
        self.session = session
        self.orders = OrderRepository(session)
        self.shipments = ShipmentRepository(session)

    def get_order_tracking(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
    ) -> OrderTrackingResult:
        # Customer-scoped lookup prevents one customer from
        # retrieving another customer's shipment information.
        order = self.orders.get_for_customer(
            order_number=order_number,
            user_id=customer_id,
        )

        if order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        shipments = (
            self.shipments.list_for_order_with_tracking(
                order.id
            )
        )

        shipment_results = []

        for shipment in shipments:
            events = sorted(
                shipment.tracking_events,
                key=lambda event: event.occurred_at,
            )

            event_results = tuple(
                TrackingEventResult(
                    status=event.status,
                    description=event.description,
                    location=event.location,
                    occurred_at=event.occurred_at,
                )
                for event in events
            )

            shipment_results.append(
                ShipmentTrackingResult(
                    tracking_number=shipment.tracking_number,
                    carrier=shipment.carrier,
                    status=shipment.status,
                    shipped_at=shipment.shipped_at,
                    estimated_delivery_at=(
                        shipment.estimated_delivery_at
                    ),
                    delivered_at=shipment.delivered_at,
                    events=event_results,
                )
            )

        return OrderTrackingResult(
            order_number=order.order_number,
            order_status=order.status,
            shipments=tuple(shipment_results),
        )