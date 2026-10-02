from __future__ import annotations

import uuid

from langchain_core.tools import tool

from src.db.session import SessionLocal
from src.services.support_ticket_service import (
    SupportTicketService,
)


def _parse_customer_id(
    customer_id: str,
) -> uuid.UUID:
    try:
        return uuid.UUID(
            customer_id
        )

    except (
        ValueError,
        TypeError,
    ) as exc:
        raise ValueError(
            "Invalid trusted customer ID."
        ) from exc


@tool
def create_support_ticket(
    customer_id: str,
    subject: str,
    description: str,
    escalation_reason: str,
    order_number: str | None = None,
) -> dict:
    """
    Create a human-support ticket for the authenticated customer.

    If an order number is supplied, ownership is verified before
    attaching the order to the ticket.
    """

    try:
        customer_uuid = (
            _parse_customer_id(
                customer_id
            )
        )

    except ValueError:
        return {
            "success": False,
            "error": "invalid_customer_id",
        }

    with SessionLocal() as session:
        service = SupportTicketService(
            session
        )

        try:
            result = service.create_ticket(
                customer_id=customer_uuid,
                subject=subject,
                description=description,
                escalation_reason=(
                    escalation_reason
                ),
                order_number=order_number,
            )

            if not result.created:
                session.rollback()

                return {
                    "success": False,
                    "error": result.reason,
                }

            session.commit()

            return {
                "success": True,
                "ticket_number": (
                    result.ticket.ticket_number
                ),
                "status": (
                    result.ticket.status
                ),
                "priority": (
                    result.ticket.priority
                ),
                "order_number": (
                    order_number
                    if order_number
                    else None
                ),
            }

        except Exception:
            session.rollback()
            raise