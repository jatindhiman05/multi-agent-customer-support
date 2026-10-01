from sqlalchemy import select

from src.db.models import Order, Refund
from src.db.session import SessionLocal
from src.services.order_service import OrderService


def main() -> None:
    with SessionLocal() as session:
        order = session.scalar(
            select(Order).where(
                Order.order_number == "ORD-1002"
            )
        )

        if order is None:
            raise RuntimeError("ORD-1002 not found.")

        customer_id = order.user_id

        print("\n--- Before cancellation ---")
        print("Order status:", order.status)

        refund_count_before = len(
            session.scalars(
                select(Refund)
                .join(Refund.payment)
                .where(
                    Refund.payment.has(
                        order_id=order.id
                    )
                )
            ).all()
        )

        print(
            "Refund count:",
            refund_count_before,
        )

        service = OrderService(session)

        print("\n--- Cancel order ---")

        result = service.cancel_order(
            order_number="ORD-1002",
            customer_id=customer_id,
        )

        print("Cancelled:", result.cancelled)
        print("Reason:", result.reason)
        print(
            "Requires refund:",
            result.requires_refund,
        )
        print(
            "Refund ID:",
            result.refund_id,
        )

        session.refresh(order)

        print(
            "Database-visible order status:",
            order.status,
        )

        refunds_after = session.scalars(
            select(Refund)
            .join(Refund.payment)
            .where(
                Refund.payment.has(
                    order_id=order.id
                )
            )
        ).all()

        print(
            "Refund count after flush:",
            len(refunds_after),
        )

        if refunds_after:
            refund = refunds_after[-1]

            print(
                "Refund status:",
                refund.status,
            )
            print(
                "Refund amount:",
                refund.amount,
                refund.currency,
            )

        print("\n--- Rollback entire transaction ---")

        session.rollback()

        session.refresh(order)

        print(
            "Order status after rollback:",
            order.status,
        )

        refunds_after_rollback = session.scalars(
            select(Refund)
            .join(Refund.payment)
            .where(
                Refund.payment.has(
                    order_id=order.id
                )
            )
        ).all()

        print(
            "Refund count after rollback:",
            len(refunds_after_rollback),
        )


if __name__ == "__main__":
    main()