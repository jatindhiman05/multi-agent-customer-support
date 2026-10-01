from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.address import Address
    from src.db.models.order import Order
    from src.db.models.return_request import ReturnRequest
    from src.db.models.support_ticket import SupportTicket

class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('customer', 'support_agent', 'admin')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "status IN ('active', 'suspended', 'disabled')",
            name="ck_users_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="customer",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
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

    addresses: Mapped[list["Address"]] = relationship(
        back_populates="user",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user",
    )

    returns: Mapped[list["ReturnRequest"]] = relationship(
        back_populates="user",
    )

    support_tickets: Mapped[list["SupportTicket"]] = relationship(
        foreign_keys="SupportTicket.user_id",
        back_populates="user",
    )

    assigned_tickets: Mapped[list["SupportTicket"]] = relationship(
        foreign_keys="SupportTicket.assigned_to",
        back_populates="assigned_agent",
    )