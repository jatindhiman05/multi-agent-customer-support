from decimal import Decimal

from sqlalchemy import select

from src.db.models import Order
from src.db.session import SessionLocal
from src.repositories.payment_repository import PaymentRepository
from src.services.refund_service import RefundService


def main() -> None:
    with SessionLocal() as session:
        payments = PaymentRepository(session)
        service = RefundService(session)

        order = session.scalar(
            select(Order).where(
                Order.order_number == "ORD-1002"
            )
        )

        if order is None:
            raise RuntimeError("ORD-1002 not found.")

        payment = payments.get_latest_captured_for_order(
            order.id
        )

        if payment is None:
            raise RuntimeError(
                "Captured payment for ORD-1002 not found."
            )

        print("\n--- Refundable balance ---")

        refundable = service.calculate_refundable_amount(
            payment
        )

        print("Payment amount:", payment.amount)
        print("Refundable amount:", refundable)

        print("\n--- Excessive refund ---")

        result = service.check_refund_eligibility(
            payment_id=payment.id,
            amount=Decimal("999.99"),
        )

        print("Allowed:", result.allowed)
        print("Reason:", result.reason)
        print(
            "Refundable amount:",
            result.refundable_amount,
        )

        print("\n--- Valid refund ---")

        result = service.create_refund(
            payment_id=payment.id,
            amount=Decimal("50.00"),
            reason="order_cancellation",
        )

        print("Created:", result.created)
        print("Reason:", result.reason)

        if result.refund is None:
            raise RuntimeError(
                "Expected refund was not created."
            )

        print("Refund ID:", result.refund.id)
        print("Refund status:", result.refund.status)
        print("Refund amount:", result.refund.amount)

        print("\n--- Balance after pending refund ---")

        refundable_after = (
            service.calculate_refundable_amount(payment)
        )

        print(
            "Refundable amount:",
            refundable_after,
        )

        print("\n--- Attempt overlapping refund ---")

        overlap = service.check_refund_eligibility(
            payment_id=payment.id,
            amount=Decimal("100.00"),
        )

        print("Allowed:", overlap.allowed)
        print("Reason:", overlap.reason)
        print(
            "Refundable amount:",
            overlap.refundable_amount,
        )

        print("\n--- Rollback ---")

        session.rollback()

        refundable_restored = (
            service.calculate_refundable_amount(payment)
        )

        print(
            "Refundable amount after rollback:",
            refundable_restored,
        )


if __name__ == "__main__":
    main()