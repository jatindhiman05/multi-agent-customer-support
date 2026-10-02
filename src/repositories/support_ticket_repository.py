from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.support_ticket import SupportTicket


class SupportTicketRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(
        self,
        ticket_id: uuid.UUID,
    ) -> SupportTicket | None:
        statement = (
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
        )

        return self.session.scalar(statement)

    def get_by_number(
        self,
        ticket_number: str,
    ) -> SupportTicket | None:
        statement = (
            select(SupportTicket)
            .where(
                SupportTicket.ticket_number == ticket_number
            )
        )

        return self.session.scalar(statement)

    def get_for_customer(
        self,
        ticket_number: str,
        user_id: uuid.UUID,
    ) -> SupportTicket | None:
        statement = (
            select(SupportTicket)
            .where(
                SupportTicket.ticket_number == ticket_number,
                SupportTicket.user_id == user_id,
            )
        )

        return self.session.scalar(statement)

    def list_for_customer(
        self,
        user_id: uuid.UUID,
    ) -> list[SupportTicket]:
        statement = (
            select(SupportTicket)
            .where(
                SupportTicket.user_id == user_id
            )
            .order_by(
                SupportTicket.created_at.desc()
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    def add(
        self,
        ticket: SupportTicket,
    ) -> SupportTicket:
        self.session.add(ticket)
        self.session.flush()

        return ticket