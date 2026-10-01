import uuid

from sqlalchemy import select

from src.db.models import Order
from src.db.session import SessionLocal
from src.repositories.order_repository import OrderRepository
from src.repositories.return_repository import ReturnRepository
from src.services.return_service import ReturnService


def get_customer_id(
    session,
    order_number: str,
):
    order = session.scalar(
        select(Order).where(
            Order.order_number == order_number
        )
    )

    if order is None:
        raise RuntimeError(
            f"{order_number} not found."
        )

    return order.user_id


def main() -> None:
    with SessionLocal() as session:
        service = ReturnService(session)
        orders = OrderRepository(session)
        returns = ReturnRepository(session)

        # =====================================================
        # TEST 1: ORD-1004
        # Existing RET-1004 already consumes the keyboard.
        # =====================================================

        customer_id_1004 = get_customer_id(
            session,
            "ORD-1004",
        )

        order_1004 = orders.get_with_details(
            order_number="ORD-1004",
            user_id=customer_id_1004,
        )

        if order_1004 is None:
            raise RuntimeError("ORD-1004 not found.")

        if not order_1004.items:
            raise RuntimeError(
                "ORD-1004 has no order items."
            )

        item_1004 = order_1004.items[0]

        print("\n--- ORD-1004 eligibility ---")

        eligibility = service.check_return_eligibility(
            order_number="ORD-1004",
            customer_id=order_1004.user_id,
            order_item_id=item_1004.id,
            quantity=1,
        )

        print("Allowed:", eligibility.allowed)
        print("Reason:", eligibility.reason)
        print(
            "Purchased:",
            eligibility.purchased_quantity,
        )
        print(
            "Consumed:",
            eligibility.consumed_quantity,
        )
        print(
            "Returnable:",
            eligibility.returnable_quantity,
        )

        # =====================================================
        # TEST 2: ORD-1001
        # Delivered order with no existing return.
        # =====================================================

        customer_id_1001 = get_customer_id(
            session,
            "ORD-1001",
        )

        order_1001 = orders.get_with_details(
            order_number="ORD-1001",
            user_id=customer_id_1001,
        )

        if order_1001 is None:
            raise RuntimeError("ORD-1001 not found.")

        if not order_1001.items:
            raise RuntimeError(
                "ORD-1001 has no order items."
            )

        item_1001 = order_1001.items[0]

        print("\n--- ORD-1001 eligibility ---")

        eligibility = service.check_return_eligibility(
            order_number="ORD-1001",
            customer_id=order_1001.user_id,
            order_item_id=item_1001.id,
            quantity=1,
        )

        print("Allowed:", eligibility.allowed)
        print("Reason:", eligibility.reason)
        print(
            "Purchased:",
            eligibility.purchased_quantity,
        )
        print(
            "Consumed:",
            eligibility.consumed_quantity,
        )
        print(
            "Returnable:",
            eligibility.returnable_quantity,
        )

        # =====================================================
        # TEST 3: Create temporary return
        # =====================================================

        print("\n--- Create return ---")

        temporary_return_number = (
            f"TEST-{uuid.uuid4().hex[:12]}"
        )

        result = service.create_return(
            order_number="ORD-1001",
            customer_id=order_1001.user_id,
            order_item_id=item_1001.id,
            quantity=1,
            return_number=temporary_return_number,
            reason="service_test",
            customer_notes="Temporary test return.",
        )

        print("Created:", result.created)
        print("Reason:", result.reason)

        if result.return_request is not None:
            print(
                "Return number:",
                result.return_request.return_number,
            )
            print(
                "Status:",
                result.return_request.status,
            )

        # =====================================================
        # TEST 4: Same item should now have no quantity left
        # =====================================================

        after = service.check_return_eligibility(
            order_number="ORD-1001",
            customer_id=order_1001.user_id,
            order_item_id=item_1001.id,
            quantity=1,
        )

        print("\n--- After temporary return ---")
        print("Allowed:", after.allowed)
        print("Reason:", after.reason)
        print("Purchased:", after.purchased_quantity)
        print("Consumed:", after.consumed_quantity)
        print("Returnable:", after.returnable_quantity)

        # =====================================================
        # TEST 5: Rollback
        # =====================================================

        print("\n--- Rollback ---")

        session.rollback()

        remaining_returns = returns.list_for_order(
            order_1001.id
        )

        temporary_exists = any(
            return_request.return_number
            == temporary_return_number
            for return_request in remaining_returns
        )

        print(
            "Temporary return exists after rollback:",
            temporary_exists,
        )


if __name__ == "__main__":
    main()