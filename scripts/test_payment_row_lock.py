import threading
import time

from sqlalchemy import select

from src.db.models import Order
from src.db.session import SessionLocal
from src.repositories.payment_repository import PaymentRepository


def transaction_a(
    payment_id,
    lock_acquired: threading.Event,
) -> None:
    with SessionLocal() as session:
        payments = PaymentRepository(session)

        print(
            "A: attempting to lock payment",
            flush=True,
        )

        payment = payments.get_by_id_for_update(
            payment_id
        )

        if payment is None:
            raise RuntimeError("Payment not found.")

        print(
            "A: lock acquired",
            flush=True,
        )

        lock_acquired.set()

        print(
            "A: holding lock for 3 seconds",
            flush=True,
        )

        time.sleep(3)

        session.rollback()

        print(
            "A: transaction rolled back; lock released",
            flush=True,
        )


def transaction_b(
    payment_id,
    lock_acquired: threading.Event,
) -> None:
    # Do not start B's lock attempt until A has definitely
    # acquired the row lock.
    lock_acquired.wait()

    with SessionLocal() as session:
        payments = PaymentRepository(session)

        print(
            "B: attempting to lock same payment",
            flush=True,
        )

        start = time.monotonic()

        payment = payments.get_by_id_for_update(
            payment_id
        )

        elapsed = time.monotonic() - start

        if payment is None:
            raise RuntimeError("Payment not found.")

        print(
            f"B: lock acquired after {elapsed:.2f} seconds",
            flush=True,
        )

        session.rollback()


def main() -> None:
    with SessionLocal() as session:
        order = session.scalar(
            select(Order).where(
                Order.order_number == "ORD-1002"
            )
        )

        if order is None:
            raise RuntimeError("ORD-1002 not found.")

        payments = PaymentRepository(session)

        payment = payments.get_latest_captured_for_order(
            order.id
        )

        if payment is None:
            raise RuntimeError(
                "Captured payment for ORD-1002 not found."
            )

        payment_id = payment.id

    lock_acquired = threading.Event()

    thread_a = threading.Thread(
        target=transaction_a,
        args=(payment_id, lock_acquired),
    )

    thread_b = threading.Thread(
        target=transaction_b,
        args=(payment_id, lock_acquired),
    )

    print("\n--- PostgreSQL row lock test ---")

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    print("\nBoth transactions finished.")


if __name__ == "__main__":
    main()