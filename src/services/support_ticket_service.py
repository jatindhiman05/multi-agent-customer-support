from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.db.models.support_ticket import SupportTicket
from src.repositories.order_repository import OrderRepository
from src.repositories.support_ticket_repository import (
    SupportTicketRepository,
)


class OrderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class TicketCreationResult:
    created: bool
    reason: str
    ticket: SupportTicket | None = None


class SupportTicketService:
    ALLOWED_ESCALATION_REASONS = {
        "human_requested",
        "unresolved_issue",
        "payment_issue",
        "delivery_issue",
        "return_issue",
        "cancellation_issue",
        "account_issue",
        "safety_concern",
        "legal_concern",
        "other",
    }

    HIGH_PRIORITY_REASONS = {
        "payment_issue",
        "safety_concern",
        "legal_concern",
    }

    URGENT_PRIORITY_REASONS = {
        "safety_concern",
    }

    def __init__(
        self,
        session: Session,
    ):
        self.session = session

        self.tickets = (
            SupportTicketRepository(session)
        )

        self.orders = OrderRepository(
            session
        )

    def _determine_priority(
        self,
        escalation_reason: str,
    ) -> str:
        if (
            escalation_reason
            in self.URGENT_PRIORITY_REASONS
        ):
            return "urgent"

        if (
            escalation_reason
            in self.HIGH_PRIORITY_REASONS
        ):
            return "high"

        return "normal"

    def _generate_ticket_number(
        self,
    ) -> str:
        return (
            f"TKT-"
            f"{uuid.uuid4().hex[:12].upper()}"
        )

    def create_ticket(
        self,
        *,
        customer_id: uuid.UUID,
        subject: str,
        description: str,
        escalation_reason: str,
        order_number: str | None = None,
    ) -> TicketCreationResult:
        subject = subject.strip()
        description = description.strip()
        escalation_reason = (
            escalation_reason.strip().lower()
        )

        # ---------------------------------------------------------
        # VALIDATE INPUT
        # ---------------------------------------------------------

        if not subject:
            return TicketCreationResult(
                created=False,
                reason="subject_required",
            )

        if not description:
            return TicketCreationResult(
                created=False,
                reason="description_required",
            )

        if len(subject) > 255:
            return TicketCreationResult(
                created=False,
                reason="subject_too_long",
            )

        if (
            escalation_reason
            not in self.ALLOWED_ESCALATION_REASONS
        ):
            return TicketCreationResult(
                created=False,
                reason="invalid_escalation_reason",
            )

        # ---------------------------------------------------------
        # OPTIONAL ORDER OWNERSHIP
        # ---------------------------------------------------------

        order_id = None

        if order_number:
            order = self.orders.get_for_customer(
                order_number=order_number,
                user_id=customer_id,
            )

            if order is None:
                return TicketCreationResult(
                    created=False,
                    reason="order_not_found",
                )

            order_id = order.id

        # ---------------------------------------------------------
        # DETERMINISTIC PRIORITY
        # ---------------------------------------------------------

        priority = self._determine_priority(
            escalation_reason
        )

        # ---------------------------------------------------------
        # CREATE TICKET
        # ---------------------------------------------------------

        ticket = SupportTicket(
            ticket_number=(
                self._generate_ticket_number()
            ),
            user_id=customer_id,
            order_id=order_id,
            assigned_to=None,
            subject=subject,
            description=description,
            status="open",
            priority=priority,
            escalation_reason=(
                escalation_reason
            ),
        )

        self.tickets.add(ticket)

        return TicketCreationResult(
            created=True,
            reason="created",
            ticket=ticket,
        )