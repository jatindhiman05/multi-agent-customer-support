from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.db.models import (
    Order,
    Payment,
    Refund,
)
from src.db.session import SessionLocal


RESET_DEFINITIONS = {
    "ORD-1002": {
        "order_status": "processing",
        "payment_status": "captured",
        "failure_code": None,
        "failure_message": None,
    },
    "ORD-1006": {
        "order_status": "pending",
        "payment_status": "failed",
        "failure_code": "card_declined",
        "failure_message": (
            "The card was declined by the issuer."
        ),
    },
}


def get_order(
    session: Session,
    order_number: str,
) -> Order | None:
    return session.scalar(
        select(Order).where(
            Order.order_number == order_number
        )
    )


def get_seed_payment(
    session: Session,
    order_number: str,
) -> Payment | None:
    transaction_id = (
        f"txn_{order_number.lower().replace('-', '_')}"
    )

    return session.scalar(
        select(Payment).where(
            Payment.provider == "stripe",
            Payment.provider_transaction_id
            == transaction_id,
        )
    )


def delete_payment_refunds(
    session: Session,
    *,
    payment: Payment,
) -> int:
    """
    Remove refunds created for this mutable demo payment.

    This intentionally affects only the payment belonging to the
    demo order currently being reset. It does not delete unrelated
    refunds.
    """

    result = session.execute(
        delete(Refund).where(
            Refund.payment_id == payment.id
        )
    )

    return result.rowcount or 0


def reset_order(
    session: Session,
    *,
    order_number: str,
    order_status: str,
    payment_status: str,
    failure_code: str | None,
    failure_message: str | None,
) -> None:
    order = get_order(
        session,
        order_number,
    )

    if order is None:
        raise RuntimeError(
            f"{order_number} does not exist. "
            "Run the development seed first."
        )

    payment = get_seed_payment(
        session,
        order_number,
    )

    if payment is None:
        raise RuntimeError(
            f"Seed payment for {order_number} "
            "does not exist. Run the development "
            "seed first."
        )

    refund_count = delete_payment_refunds(
        session,
        payment=payment,
    )

    order.status = order_status

    payment.status = payment_status
    payment.failure_code = failure_code
    payment.failure_message = failure_message

    print(
        f"{order_number}: "
        f"order -> {order_status}, "
        f"payment -> {payment_status}, "
        f"refunds removed -> {refund_count}"
    )


def reset_demo_orders() -> None:
    with SessionLocal() as session:
        try:
            for (
                order_number,
                definition,
            ) in RESET_DEFINITIONS.items():
                reset_order(
                    session,
                    order_number=order_number,
                    **definition,
                )

            session.commit()

            print(
                "Mutable demo orders reset "
                "successfully."
            )

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    reset_demo_orders()