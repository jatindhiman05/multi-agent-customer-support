from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.order import Order
    from src.db.models.user import User


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    __table_args__ = (
        CheckConstraint(
            """
            status IN (
                'open',
                'in_progress',
                'resolved',
                'closed'
            )
            """,
            name="ck_support_tickets_status",
        ),
        CheckConstraint(
            """
            priority IN (
                'low',
                'normal',
                'high',
                'urgent'
            )
            """,
            name="ck_support_tickets_priority",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    ticket_number: Mapped[str] = mapped_column(
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

    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=True,
        index=True,
    )

    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="normal",
    )

    escalation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
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

    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
        back_populates="support_tickets",
    )

    assigned_agent: Mapped["User | None"] = relationship(
        foreign_keys=[assigned_to],
        back_populates="assigned_tickets",
    )

    order: Mapped["Order | None"] = relationship(
        back_populates="support_tickets",
    )