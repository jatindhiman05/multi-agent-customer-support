from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.db.models import Order, OrderItem, Shipment
from src.db.session import SessionLocal
from src.services.return_service import ReturnService


def main():
    with SessionLocal() as session:
        # --------------------------------------------------------------
        # Find ORD-1004
        # --------------------------------------------------------------

        order = session.execute(
            select(Order).where(
                Order.order_number == "ORD-1004"
            )
        ).scalar_one()

        order_item = session.execute(
            select(OrderItem).where(
                OrderItem.order_id == order.id
            )
        ).scalars().first()

        shipment = session.execute(
            select(Shipment).where(
                Shipment.order_id == order.id
            )
        ).scalars().first()

        if order_item is None:
            raise RuntimeError("ORD-1004 has no order item.")

        if shipment is None:
            raise RuntimeError("ORD-1004 has no shipment.")

        original_delivered_at = shipment.delivered_at

        print("Order:", order.order_number)
        print("Original delivered_at:", original_delivered_at)

        # --------------------------------------------------------------
        # Temporarily make delivery older than the 30-day window
        # --------------------------------------------------------------

        shipment.delivered_at = (
            datetime.now(timezone.utc) - timedelta(days=31)
        )

        session.flush()

        print("Temporary delivered_at:", shipment.delivered_at)

        # --------------------------------------------------------------
        # Check eligibility
        # --------------------------------------------------------------

        service = ReturnService(session)

        eligibility = service.check_return_eligibility(
            order_number=order.order_number,
            customer_id=order.user_id,
            order_item_id=order_item.id,
            quantity=1,
        )

        print()
        print("Allowed:", eligibility.allowed)
        print("Reason:", eligibility.reason)
        print(
            "Returnable quantity:",
            eligibility.returnable_quantity,
        )

        # --------------------------------------------------------------
        # IMPORTANT:
        # Never persist our fake delivery timestamp.
        # --------------------------------------------------------------

        session.rollback()

        print()
        print("Rolled back temporary delivery-date change.")


if __name__ == "__main__":
    main()