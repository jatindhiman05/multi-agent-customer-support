from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.db.models import Shipment


class ShipmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(
        self,
        shipment_id: uuid.UUID,
    ) -> Shipment | None:
        statement = (
            select(Shipment)
            .where(Shipment.id == shipment_id)
        )

        return self.session.scalar(statement)

    def get_by_tracking_number(
        self,
        tracking_number: str,
    ) -> Shipment | None:
        statement = (
            select(Shipment)
            .where(
                Shipment.tracking_number == tracking_number
            )
        )

        return self.session.scalar(statement)

    def list_for_order(
        self,
        order_id: uuid.UUID,
    ) -> list[Shipment]:
        statement = (
            select(Shipment)
            .where(Shipment.order_id == order_id)
            .order_by(Shipment.created_at.asc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def list_for_order_with_tracking(
        self,
        order_id: uuid.UUID,
    ) -> list[Shipment]:
        statement = (
            select(Shipment)
            .options(
                selectinload(Shipment.tracking_events),
                selectinload(Shipment.items),
            )
            .where(Shipment.order_id == order_id)
            .order_by(Shipment.created_at.asc())
        )

        return list(
            self.session.scalars(statement).all()
        )