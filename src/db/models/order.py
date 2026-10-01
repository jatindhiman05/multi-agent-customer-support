from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from src.db.models.payment import Payment
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.models.shipment import Shipment
from src.db.base import Base
from src.db.models.return_request import ReturnRequest
if TYPE_CHECKING:
    from src.db.models.order_item import OrderItem
    from src.db.models.user import User


class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            """
            status IN (
                'pending',
                'confirmed',
                'processing',
                'shipped',
                'delivered',
                'cancelled'
            )
            """,
            name="ck_orders_status",
        ),
        CheckConstraint(
            "subtotal >= 0",
            name="ck_orders_subtotal_non_negative",
        ),
        CheckConstraint(
            "shipping_amount >= 0",
            name="ck_orders_shipping_amount_non_negative",
        ),
        CheckConstraint(
            "tax_amount >= 0",
            name="ck_orders_tax_amount_non_negative",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="ck_orders_discount_amount_non_negative",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_amount_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    order_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    shipping_recipient_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    shipping_line1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    shipping_line2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    shipping_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    shipping_state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    shipping_postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    shipping_country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    shipping_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(
        back_populates="orders",
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
    )

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order",
    )
    shipments: Mapped[list["Shipment"]] = relationship(
        back_populates="order",
    )
    returns: Mapped[list["ReturnRequest"]] = relationship(
        back_populates="order",
    )