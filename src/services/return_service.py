from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.db.models import OrderItem, ReturnItem, ReturnRequest
from src.repositories.order_repository import OrderRepository
from src.repositories.return_repository import ReturnRepository


class OrderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class ReturnEligibility:
    allowed: bool
    reason: str
    purchased_quantity: int
    consumed_quantity: int
    returnable_quantity: int


@dataclass(frozen=True)
class ReturnResult:
    created: bool
    reason: str
    return_request: ReturnRequest | None


class ReturnService:
    RETURNABLE_ORDER_STATUSES = {
        "delivered",
    }

    def __init__(self, session: Session):
        self.session = session
        self.orders = OrderRepository(session)
        self.returns = ReturnRepository(session)

    def _find_order_item(
        self,
        order_items: list[OrderItem],
        order_item_id: uuid.UUID,
    ) -> OrderItem | None:
        for order_item in order_items:
            if order_item.id == order_item_id:
                return order_item

        return None

    def _calculate_consumed_quantity(
        self,
        order_item_id: uuid.UUID,
    ) -> int:
        return_items = (
            self.returns.list_items_for_order_item(
                order_item_id
            )
        )

        return sum(
            return_item.quantity
            for return_item in return_items
        )

    def check_return_eligibility(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
        order_item_id: uuid.UUID,
        quantity: int,
    ) -> ReturnEligibility:
        order = self.orders.get_for_customer(
            order_number=order_number,
            user_id=customer_id,
        )

        if order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        # Load items explicitly through the existing detailed lookup.
        detailed_order = self.orders.get_with_details(
            order_number=order_number,
            user_id=customer_id,
        )

        if detailed_order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        order_item = self._find_order_item(
            detailed_order.items,
            order_item_id,
        )

        if order_item is None:
            return ReturnEligibility(
                allowed=False,
                reason="item_not_in_order",
                purchased_quantity=0,
                consumed_quantity=0,
                returnable_quantity=0,
            )

        consumed_quantity = (
            self._calculate_consumed_quantity(
                order_item.id
            )
        )

        returnable_quantity = max(
            order_item.quantity - consumed_quantity,
            0,
        )

        if order.status not in self.RETURNABLE_ORDER_STATUSES:
            return ReturnEligibility(
                allowed=False,
                reason="order_not_delivered",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=returnable_quantity,
            )

        if quantity <= 0:
            return ReturnEligibility(
                allowed=False,
                reason="invalid_return_quantity",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=returnable_quantity,
            )

        if returnable_quantity <= 0:
            return ReturnEligibility(
                allowed=False,
                reason="nothing_left_to_return",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=0,
            )

        if quantity > returnable_quantity:
            return ReturnEligibility(
                allowed=False,
                reason="quantity_exceeds_returnable_amount",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=returnable_quantity,
            )

        return ReturnEligibility(
            allowed=True,
            reason="return_allowed",
            purchased_quantity=order_item.quantity,
            consumed_quantity=consumed_quantity,
            returnable_quantity=returnable_quantity,
        )

    def create_return(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
        order_item_id: uuid.UUID,
        quantity: int,
        return_number: str,
        reason: str,
        customer_notes: str | None = None,
    ) -> ReturnResult:
        # Mutation path: lock the order first.
        order = self.orders.get_for_customer_for_update(
            order_number=order_number,
            user_id=customer_id,
        )

        if order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        order_item = self._find_order_item(
            order.items,
            order_item_id,
        )

        if order_item is None:
            return ReturnResult(
                created=False,
                reason="item_not_in_order",
                return_request=None,
            )

        consumed_quantity = (
            self._calculate_consumed_quantity(
                order_item.id
            )
        )

        returnable_quantity = max(
            order_item.quantity - consumed_quantity,
            0,
        )

        # Revalidate everything while holding the lock.
        if order.status not in self.RETURNABLE_ORDER_STATUSES:
            return ReturnResult(
                created=False,
                reason="order_not_delivered",
                return_request=None,
            )

        if quantity <= 0:
            return ReturnResult(
                created=False,
                reason="invalid_return_quantity",
                return_request=None,
            )

        if returnable_quantity <= 0:
            return ReturnResult(
                created=False,
                reason="nothing_left_to_return",
                return_request=None,
            )

        if quantity > returnable_quantity:
            return ReturnResult(
                created=False,
                reason="quantity_exceeds_returnable_amount",
                return_request=None,
            )

        return_request = ReturnRequest(
            return_number=return_number,
            order_id=order.id,
            user_id=customer_id,
            status="requested",
            reason=reason,
            customer_notes=customer_notes,
        )

        self.returns.add(return_request)

        return_item = ReturnItem(
            return_id=return_request.id,
            order_item_id=order_item.id,
            quantity=quantity,
        )

        self.returns.add_item(return_item)

        return ReturnResult(
            created=True,
            reason="return_created",
            return_request=return_request,
        )