from sqlalchemy import select

from src.db.models import Order
from src.db.session import SessionLocal
from src.repositories.return_repository import ReturnRepository


def main() -> None:
    with SessionLocal() as session:
        repository = ReturnRepository(session)

        # -----------------------------------------------------
        # EXISTING RETURN: RET-1004
        # -----------------------------------------------------

        print("\n--- RET-1004 ---")

        return_request = repository.get_by_number(
            "RET-1004"
        )

        if return_request is None:
            raise RuntimeError("RET-1004 not found.")

        print("Return:", return_request.return_number)
        print("Status:", return_request.status)
        print("Reason:", return_request.reason)

        # -----------------------------------------------------
        # CUSTOMER-SCOPED LOOKUP
        # -----------------------------------------------------

        print("\n--- Customer-scoped return ---")

        customer_return = repository.get_for_customer(
            return_number="RET-1004",
            user_id=return_request.user_id,
        )

        print(
            "Found:",
            customer_return is not None,
        )

        # -----------------------------------------------------
        # ORDER RETURNS
        # -----------------------------------------------------

        order = session.scalar(
            select(Order).where(
                Order.order_number == "ORD-1004"
            )
        )

        if order is None:
            raise RuntimeError("ORD-1004 not found.")

        returns = repository.list_for_order(order.id)

        print("\n--- ORD-1004 returns ---")
        print("Return count:", len(returns))

        for item in returns:
            print(
                item.return_number,
                item.status,
            )

        # -----------------------------------------------------
        # RETURN DETAILS
        # -----------------------------------------------------

        details = repository.get_with_details(
            return_number="RET-1004",
            user_id=return_request.user_id,
        )

        if details is None:
            raise RuntimeError(
                "RET-1004 details not found."
            )

        print("\n--- RET-1004 details ---")
        print("Item count:", len(details.items))
        print("Refund count:", len(details.refunds))

        for return_item in details.items:
            print(
                "Return item:",
                return_item.order_item_id,
                "quantity:",
                return_item.quantity,
            )

        # -----------------------------------------------------
        # QUANTITY-CONSUMING RETURNS
        # -----------------------------------------------------

        if not details.items:
            raise RuntimeError(
                "RET-1004 has no return items."
            )

        order_item_id = details.items[0].order_item_id

        consuming_items = (
            repository.list_items_for_order_item(
                order_item_id
            )
        )

        print("\n--- Quantity-consuming returns ---")
        print(
            "Return item count:",
            len(consuming_items),
        )

        print(
            "Consumed quantity:",
            sum(
                item.quantity
                for item in consuming_items
            ),
        )


if __name__ == "__main__":
    main()