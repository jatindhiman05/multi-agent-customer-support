from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.order_item import OrderItem
    from src.db.models.shipment import Shipment


class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_shipment_items_quantity_positive",
        ),
        UniqueConstraint(
            "shipment_id",
            "order_item_id",
            name="uq_shipment_items_shipment_order_item",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id"),
        nullable=False,
        index=True,
    )

    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order_items.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    shipment: Mapped["Shipment"] = relationship(
        back_populates="items",
    )

    order_item: Mapped["OrderItem"] = relationship(
        back_populates="shipment_items",
    )