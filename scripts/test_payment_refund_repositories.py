from sqlalchemy import select
from decimal import Decimal

from src.db.models import Order, Refund
from src.db.session import SessionLocal
from src.repositories.payment_repository import PaymentRepository
from src.repositories.refund_repository import RefundRepository


def main() -> None:
    with SessionLocal() as session:
        payments = PaymentRepository(session)
        refunds = RefundRepository(session)

        # ---------------------------------------------------------
        # ORD-1002
        # Captured payment, no existing refund
        # ---------------------------------------------------------

        print("\n--- ORD-1002 payment ---")

        order_1002 = session.scalar(
            select(Order).where(
                Order.order_number == "ORD-1002"
            )
        )

        if order_1002 is None:
            raise RuntimeError("ORD-1002 not found.")

        order_payments = payments.list_for_order(
            order_1002.id
        )

        print(
            "Payment count:",
            len(order_payments),
        )

        for payment in order_payments:
            print(
                "Payment:",
                payment.provider,
                payment.status,
                payment.amount,
                payment.currency,
            )

        captured_payment = (
            payments.get_latest_captured_for_order(
                order_1002.id
            )
        )

        if captured_payment is None:
            raise RuntimeError(
                "Captured payment for ORD-1002 not found."
            )

        print(
            "Captured payment:",
            captured_payment.status,
        )

        existing_refunds = refunds.list_for_payment(
            captured_payment.id
        )

        print(
            "Existing refunds:",
            len(existing_refunds),
        )

                # ---------------------------------------------------------
        # CREATE REFUND INSIDE TRANSACTION
        # ---------------------------------------------------------

        print("\n--- Create refund transaction ---")

        new_refund = Refund(
            payment_id=captured_payment.id,
            return_id=None,
            provider=captured_payment.provider,
            provider_refund_id="test_refund_ord_1002",
            status="pending",
            amount=Decimal(str(captured_payment.amount)),
            currency=captured_payment.currency,
            reason="order_cancellation",
        )

        created_refund = refunds.add(new_refund)

        print(
            "Created refund ID:",
            created_refund.id,
        )
        print(
            "Status:",
            created_refund.status,
        )
        print(
            "Amount:",
            created_refund.amount,
            created_refund.currency,
        )

        refunds_after_create = refunds.list_for_payment(
            captured_payment.id
        )

        print(
            "Refund count after flush:",
            len(refunds_after_create),
        )

        # Undo the test mutation.
        session.rollback()

        refunds_after_rollback = refunds.list_for_payment(
            captured_payment.id
        )

        print(
            "Refund count after rollback:",
            len(refunds_after_rollback),
        )
        # ---------------------------------------------------------
        # ORD-1005
        # Already has completed refund
        # ---------------------------------------------------------

        print("\n--- ORD-1005 refund ---")

        order_1005 = session.scalar(
            select(Order).where(
                Order.order_number == "ORD-1005"
            )
        )

        if order_1005 is None:
            raise RuntimeError("ORD-1005 not found.")

        captured_payment_1005 = (
            payments.get_latest_captured_for_order(
                order_1005.id
            )
        )

        if captured_payment_1005 is None:
            raise RuntimeError(
                "Payment for ORD-1005 not found."
            )

        existing_refunds_1005 = refunds.list_for_payment(
            captured_payment_1005.id
        )

        print(
            "Refund count:",
            len(existing_refunds_1005),
        )

        for refund in existing_refunds_1005:
            print(
                "Refund:",
                refund.status,
                refund.amount,
                refund.currency,
            )


if __name__ == "__main__":
    main()