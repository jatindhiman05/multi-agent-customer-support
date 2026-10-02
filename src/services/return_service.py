from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import (
    OrderItem,
    ReturnItem,
    ReturnRequest,
    Shipment,
    ShipmentItem,
)
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
    """
    Business logic for customer returns.

    Important:
    - Customer ownership is always enforced.
    - Only delivered orders are returnable.
    - Items must be returned within 30 days of delivery.
    - Previously returned quantities cannot be returned again.
    - Mutation paths revalidate all important rules while holding
      an order-level row lock.
    """

    RETURNABLE_ORDER_STATUSES = {
        "delivered",
    }

    RETURN_WINDOW_DAYS = 30

    def __init__(self, session: Session):
        self.session = session
        self.orders = OrderRepository(session)
        self.returns = ReturnRepository(session)

    # =====================================================================
    # INTERNAL HELPERS
    # =====================================================================

    def _find_order_item(
        self,
        order_items: list[OrderItem],
        order_item_id: uuid.UUID,
    ) -> OrderItem | None:
        """
        Find a specific order item from an order's items.
        """

        for order_item in order_items:
            if order_item.id == order_item_id:
                return order_item

        return None

    def _calculate_consumed_quantity(
        self,
        order_item_id: uuid.UUID,
    ) -> int:
        """
        Calculate how many units of an order item have already been
        consumed by existing active/completed return requests.

        ReturnRepository is responsible for excluding statuses such as
        rejected/cancelled where appropriate.
        """

        return_items = self.returns.list_items_for_order_item(
            order_item_id
        )

        return sum(
            return_item.quantity
            for return_item in return_items
        )

    def _get_item_delivered_at(
        self,
        order_item_id: uuid.UUID,
    ) -> datetime | None:
        """
        Find the delivery timestamp for a specific order item.

        We intentionally resolve delivery through ShipmentItem instead
        of using only the overall order status because an order may be
        split across multiple shipments.

        If an item appears in multiple delivered shipments, the most
        recent delivery timestamp is used for now.
        """

        stmt = (
            select(Shipment.delivered_at)
            .join(
                ShipmentItem,
                ShipmentItem.shipment_id == Shipment.id,
            )
            .where(
                ShipmentItem.order_item_id == order_item_id,
                Shipment.status == "delivered",
                Shipment.delivered_at.is_not(None),
            )
            .order_by(Shipment.delivered_at.desc())
            .limit(1)
        )

        return self.session.execute(
            stmt
        ).scalar_one_or_none()

    def _is_return_window_expired(
        self,
        delivered_at: datetime,
    ) -> bool:
        """
        Return True when the configured return window has expired.
        """

        return_deadline = delivered_at + timedelta(
            days=self.RETURN_WINDOW_DAYS
        )

        return datetime.now(timezone.utc) > return_deadline

    # =====================================================================
    # READ-ONLY ELIGIBILITY CHECK
    # =====================================================================

    def check_return_eligibility(
        self,
        *,
        order_number: str,
        customer_id: uuid.UUID,
        order_item_id: uuid.UUID,
        quantity: int,
    ) -> ReturnEligibility:
        """
        Check whether the requested quantity of an order item can
        currently be returned.

        This method performs no mutation.
        """

        # -----------------------------------------------------------------
        # 1. Customer-scoped order lookup
        # -----------------------------------------------------------------

        order = self.orders.get_for_customer(
            order_number=order_number,
            user_id=customer_id,
        )

        if order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        # -----------------------------------------------------------------
        # 2. Load complete order details
        # -----------------------------------------------------------------

        detailed_order = self.orders.get_with_details(
            order_number=order_number,
            user_id=customer_id,
        )

        if detailed_order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        # -----------------------------------------------------------------
        # 3. Verify item belongs to this order
        # -----------------------------------------------------------------

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

        # -----------------------------------------------------------------
        # 4. Calculate already-returned quantity
        # -----------------------------------------------------------------

        consumed_quantity = self._calculate_consumed_quantity(
            order_item.id
        )

        returnable_quantity = max(
            order_item.quantity - consumed_quantity,
            0,
        )

        # -----------------------------------------------------------------
        # 5. Order must be delivered
        # -----------------------------------------------------------------

        if order.status not in self.RETURNABLE_ORDER_STATUSES:
            return ReturnEligibility(
                allowed=False,
                reason="order_not_delivered",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=returnable_quantity,
            )

        # -----------------------------------------------------------------
        # 6. Delivery timestamp must exist
        # -----------------------------------------------------------------

        delivered_at = self._get_item_delivered_at(
            order_item.id
        )

        if delivered_at is None:
            return ReturnEligibility(
                allowed=False,
                reason="delivery_date_unavailable",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=returnable_quantity,
            )

        # -----------------------------------------------------------------
        # 7. Enforce 30-day return window
        # -----------------------------------------------------------------

        if self._is_return_window_expired(delivered_at):
            return ReturnEligibility(
                allowed=False,
                reason="return_window_expired",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=returnable_quantity,
            )

        # -----------------------------------------------------------------
        # 8. Quantity must be positive
        # -----------------------------------------------------------------

        if quantity <= 0:
            return ReturnEligibility(
                allowed=False,
                reason="invalid_return_quantity",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=returnable_quantity,
            )

        # -----------------------------------------------------------------
        # 9. Something must still be returnable
        # -----------------------------------------------------------------

        if returnable_quantity <= 0:
            return ReturnEligibility(
                allowed=False,
                reason="nothing_left_to_return",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=0,
            )

        # -----------------------------------------------------------------
        # 10. Requested quantity cannot exceed remaining quantity
        # -----------------------------------------------------------------

        if quantity > returnable_quantity:
            return ReturnEligibility(
                allowed=False,
                reason="quantity_exceeds_returnable_amount",
                purchased_quantity=order_item.quantity,
                consumed_quantity=consumed_quantity,
                returnable_quantity=returnable_quantity,
            )

        # -----------------------------------------------------------------
        # Eligible
        # -----------------------------------------------------------------

        return ReturnEligibility(
            allowed=True,
            reason="return_allowed",
            purchased_quantity=order_item.quantity,
            consumed_quantity=consumed_quantity,
            returnable_quantity=returnable_quantity,
        )

    # =====================================================================
    # MUTATION
    # =====================================================================

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
        """
        Create a return request.

        The mutation path locks the order and independently revalidates
        the important business rules before writing anything.

        The caller owns commit/rollback.
        """

        # -----------------------------------------------------------------
        # 1. Lock customer-owned order
        # -----------------------------------------------------------------

        order = self.orders.get_for_customer_for_update(
            order_number=order_number,
            user_id=customer_id,
        )

        if order is None:
            raise OrderNotFoundError(
                f"Order {order_number} was not found."
            )

        # -----------------------------------------------------------------
        # 2. Verify item belongs to order
        # -----------------------------------------------------------------

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

        # -----------------------------------------------------------------
        # 3. Recalculate consumed quantity while mutation is protected
        # -----------------------------------------------------------------

        consumed_quantity = self._calculate_consumed_quantity(
            order_item.id
        )

        returnable_quantity = max(
            order_item.quantity - consumed_quantity,
            0,
        )

        # -----------------------------------------------------------------
        # 4. Revalidate order status
        # -----------------------------------------------------------------

        if order.status not in self.RETURNABLE_ORDER_STATUSES:
            return ReturnResult(
                created=False,
                reason="order_not_delivered",
                return_request=None,
            )

        # -----------------------------------------------------------------
        # 5. Revalidate delivery timestamp
        # -----------------------------------------------------------------

        delivered_at = self._get_item_delivered_at(
            order_item.id
        )

        if delivered_at is None:
            return ReturnResult(
                created=False,
                reason="delivery_date_unavailable",
                return_request=None,
            )

        # -----------------------------------------------------------------
        # 6. Revalidate 30-day return window
        # -----------------------------------------------------------------

        if self._is_return_window_expired(delivered_at):
            return ReturnResult(
                created=False,
                reason="return_window_expired",
                return_request=None,
            )

        # -----------------------------------------------------------------
        # 7. Revalidate requested quantity
        # -----------------------------------------------------------------

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

        # -----------------------------------------------------------------
        # 8. Create return request
        # -----------------------------------------------------------------

        return_request = ReturnRequest(
            return_number=return_number,
            order_id=order.id,
            user_id=customer_id,
            status="requested",
            reason=reason,
            customer_notes=customer_notes,
        )

        self.returns.add(return_request)

        # -----------------------------------------------------------------
        # 9. Create return item
        # -----------------------------------------------------------------

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