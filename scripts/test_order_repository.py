from sqlalchemy import select

from src.db.models import User
from src.db.session import SessionLocal
from src.repositories.order_repository import OrderRepository


def main() -> None:
    with SessionLocal() as session:
        customer = session.scalar(
            select(User).where(
                User.email == "alex@example.com"
            )
        )

        if customer is None:
            raise RuntimeError("Seed customer not found.")

        repository = OrderRepository(session)

        print("\n--- Get by number ---")

        order = repository.get_by_number("ORD-1003")

        if order is None:
            raise RuntimeError("ORD-1003 not found.")

        print(order.order_number)
        print(order.status)

        print("\n--- Customer ownership lookup ---")

        owned_order = repository.get_for_customer(
            "ORD-1003",
            customer.id,
        )

        print(
            owned_order.order_number
            if owned_order
            else "Not found"
        )

        print("\n--- Customer orders ---")

        orders = repository.list_for_customer(customer.id)

        for customer_order in orders:
            print(
                customer_order.order_number,
                customer_order.status,
            )

        print("\n--- Order details ---")

        detailed_order = repository.get_with_details(
            "ORD-1003",
            customer.id,
        )

        if detailed_order is None:
            raise RuntimeError("Detailed order not found.")

        print("Order:", detailed_order.order_number)
        print("Items:", len(detailed_order.items))
        print("Payments:", len(detailed_order.payments))
        print("Shipments:", len(detailed_order.shipments))
        print("Returns:", len(detailed_order.returns))

        print("\n--- Ownership isolation ---")

        agent = session.scalar(
            select(User).where(
                User.email == "maya.agent@voltnest.example"
            )
        )

        if agent is None:
            raise RuntimeError("Seed support agent not found.")

        unauthorized_order = repository.get_for_customer(
            "ORD-1003",
            agent.id,
        )

        print(
            "Access blocked"
            if unauthorized_order is None
            else "ERROR: Unauthorized order returned"
        )


if __name__ == "__main__":
    main()