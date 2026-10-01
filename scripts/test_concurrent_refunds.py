import threading
import time
from decimal import Decimal

from sqlalchemy import select

from src.db.models import Order, Refund
from src.db.session import SessionLocal
from src.repositories.payment_repository import PaymentRepository
from src.services.refund_service import RefundService


def refund_worker(
    name: str,
    payment_id,
    start_event: threading.Event,
) -> None:
    with SessionLocal() as session:
        service = RefundService(session)

        # Both threads wait here so that we can release them
        # at approximately the same time.
        start_event.wait()

        print(
            f"{name}: attempting full refund",
            flush=True,
        )

        start = time.monotonic()

        result = service.create_refund(
            payment_id=payment_id,
            amount=Decimal("134.59"),
            reason="concurrency_test",
        )

        elapsed = time.monotonic() - start

        print(
            f"{name}: created={result.created}, "
            f"reason={result.reason}, "
            f"elapsed={elapsed:.2f}s",
            flush=True,
        )

        if result.created:
            # Hold the transaction briefly.
            #
            # The other transaction should remain blocked on
            # SELECT ... FOR UPDATE until this transaction ends.
            time.sleep(2)

            session.commit()

            print(
                f"{name}: committed",
                flush=True,
            )
        else:
            session.rollback()

            print(
                f"{name}: rolled back",
                flush=True,
            )


def main() -> None:
    # ---------------------------------------------------------
    # FIND ORD-1002 PAYMENT
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # START CONCURRENT REQUESTS
    # ---------------------------------------------------------

    start_event = threading.Event()

    thread_a = threading.Thread(
        target=refund_worker,
        args=(
            "A",
            payment_id,
            start_event,
        ),
    )

    thread_b = threading.Thread(
        target=refund_worker,
        args=(
            "B",
            payment_id,
            start_event,
        ),
    )

    print("\n--- Concurrent refund test ---")

    thread_a.start()
    thread_b.start()

    # Both threads are now waiting on start_event.
    start_event.set()

    thread_a.join()
    thread_b.join()

    # ---------------------------------------------------------
    # VERIFY DATABASE STATE
    # ---------------------------------------------------------

    with SessionLocal() as session:
        refunds = session.scalars(
            select(Refund).where(
                Refund.payment_id == payment_id,
                Refund.reason == "concurrency_test",
            )
        ).all()

        print("\n--- Final database state ---")
        print(
            "Concurrency-test refunds:",
            len(refunds),
        )

        for refund in refunds:
            print(
                refund.id,
                refund.status,
                refund.amount,
            )

        # IMPORTANT:
        # This test intentionally committed one refund so we could
        # test real cross-transaction behavior.
        #
        # Clean up only the test refund.
        for refund in refunds:
            session.delete(refund)

        session.commit()

        print(
            "Concurrency-test data cleaned up."
        )


if __name__ == "__main__":
    main()