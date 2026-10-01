from sqlalchemy import select

from src.db.models import User
from src.db.session import SessionLocal
from src.services.order_service import (
    OrderNotFoundError,
    OrderService,
)


def main() -> None:
    with SessionLocal() as session:
        customer = session.scalar(
            select(User).where(
                User.email == "alex@example.com"
            )
        )

        agent = session.scalar(
            select(User).where(
                User.email == "maya.agent@voltnest.example"
            )
        )

        if customer is None:
            raise RuntimeError("Seed customer not found.")

        if agent is None:
            raise RuntimeError("Seed support agent not found.")

        service = OrderService(session)

        # ---------------------------------------------------------
        # ORDER LOOKUP
        # ---------------------------------------------------------

        print("\n--- Order lookup ---")

        order = service.get_order(
            order_number="ORD-1003",
            customer_id=customer.id,
        )

        print("Order:", order.order_number)
        print("Status:", order.status)

        # ---------------------------------------------------------
        # CANCELLATION ELIGIBILITY
        # ---------------------------------------------------------

        print("\n--- Cancellation eligibility ---")

        for order_number in [
            "ORD-1001",
            "ORD-1002",
            "ORD-1003",
            "ORD-1006",
        ]:
            result = service.check_cancellation_eligibility(
                order_number=order_number,
                customer_id=customer.id,
            )

            print(
                order_number,
                "| allowed:",
                result.allowed,
                "| reason:",
                result.reason,
            )

        # ---------------------------------------------------------
        # OWNERSHIP ISOLATION
        # ---------------------------------------------------------

        print("\n--- Unauthorized ownership lookup ---")

        try:
            service.get_order(
                order_number="ORD-1003",
                customer_id=agent.id,
            )

            print("ERROR: Unauthorized order returned")

        except OrderNotFoundError:
            print("Access blocked")

        # ---------------------------------------------------------
        # MISSING ORDER
        # ---------------------------------------------------------

        print("\n--- Missing order ---")

        try:
            service.get_order(
                order_number="ORD-9999",
                customer_id=customer.id,
            )

            print("ERROR: Missing order returned")

        except OrderNotFoundError:
            print("Order not found handled correctly")


if __name__ == "__main__":
    main()