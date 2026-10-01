from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.models.refund import Refund
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.order import Order
    from src.db.models.return_item import ReturnItem
    from src.db.models.user import User


class ReturnRequest(Base):
    __tablename__ = "returns"

    __table_args__ = (
        CheckConstraint(
            """
            status IN (
                'requested',
                'approved',
                'rejected',
                'in_transit',
                'received',
                'completed',
                'cancelled'
            )
            """,
            name="ck_returns_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    return_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
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
        default="requested",
    )

    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    customer_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    order: Mapped["Order"] = relationship(
        back_populates="returns",
    )

    user: Mapped["User"] = relationship(
        back_populates="returns",
    )

    items: Mapped[list["ReturnItem"]] = relationship(
        back_populates="return_request",
    )

    refunds: Mapped[list["Refund"]] = relationship(
        back_populates="return_request",
    )