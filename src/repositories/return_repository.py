from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.db.models import ReturnItem, ReturnRequest


class ReturnRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(
        self,
        return_id: uuid.UUID,
    ) -> ReturnRequest | None:
        statement = (
            select(ReturnRequest)
            .where(ReturnRequest.id == return_id)
        )

        return self.session.scalar(statement)

    def get_by_number(
        self,
        return_number: str,
    ) -> ReturnRequest | None:
        statement = (
            select(ReturnRequest)
            .where(
                ReturnRequest.return_number == return_number
            )
        )

        return self.session.scalar(statement)

    def get_for_customer(
        self,
        return_number: str,
        user_id: uuid.UUID,
    ) -> ReturnRequest | None:
        statement = (
            select(ReturnRequest)
            .where(
                ReturnRequest.return_number == return_number,
                ReturnRequest.user_id == user_id,
            )
        )

        return self.session.scalar(statement)

    def list_for_order(
        self,
        order_id: uuid.UUID,
    ) -> list[ReturnRequest]:
        statement = (
            select(ReturnRequest)
            .where(ReturnRequest.order_id == order_id)
            .order_by(ReturnRequest.created_at.asc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def list_for_customer(
        self,
        user_id: uuid.UUID,
    ) -> list[ReturnRequest]:
        statement = (
            select(ReturnRequest)
            .where(ReturnRequest.user_id == user_id)
            .order_by(ReturnRequest.created_at.desc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_with_details(
        self,
        return_number: str,
        user_id: uuid.UUID,
    ) -> ReturnRequest | None:
        statement = (
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.items),
                selectinload(ReturnRequest.refunds),
            )
            .where(
                ReturnRequest.return_number == return_number,
                ReturnRequest.user_id == user_id,
            )
        )

        return self.session.scalar(statement)

    def list_items_for_order_item(
        self,
        order_item_id: uuid.UUID,
    ) -> list[ReturnItem]:
        statement = (
            select(ReturnItem)
            .join(ReturnRequest)
            .where(
                ReturnItem.order_item_id == order_item_id,
                ReturnRequest.status.notin_(
                    {"rejected", "cancelled"}
                ),
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    def add(
        self,
        return_request: ReturnRequest,
    ) -> ReturnRequest:
        self.session.add(return_request)
        self.session.flush()

        return return_request

    def add_item(
        self,
        return_item: ReturnItem,
    ) -> ReturnItem:
        self.session.add(return_item)
        self.session.flush()

        return return_item

    def set_status(
        self,
        return_request: ReturnRequest,
        status: str,
    ) -> None:
        return_request.status = status
        self.session.flush()