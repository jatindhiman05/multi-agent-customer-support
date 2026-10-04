from __future__ import annotations

import uuid

from langchain_core.messages import HumanMessage
from sqlalchemy import select

from src.db.models import Order, Refund
from src.db.session import SessionLocal
from src.graph.graph import support_graph


ORDER_NUMBER = "ORD-1002"


# =============================================================================
# DATABASE HELPERS
# =============================================================================


def get_order_snapshot() -> dict:
    """
    Read committed database state for the test order.
    """

    with SessionLocal() as session:
        order = session.scalar(
            select(Order).where(
                Order.order_number == ORDER_NUMBER
            )
        )

        if order is None:
            raise RuntimeError(
                f"{ORDER_NUMBER} not found. "
                "Seed/reset the demo database first."
            )

        refunds = session.scalars(
            select(Refund)
            .join(Refund.payment)
            .where(
                Refund.payment.has(
                    order_id=order.id
                )
            )
        ).all()

        return {
            "order_id": order.id,
            "customer_id": order.user_id,
            "status": order.status,
            "refund_count": len(refunds),
        }


def assert_database_unchanged(
    *,
    expected_status: str,
    expected_refund_count: int,
) -> None:
    snapshot = get_order_snapshot()

    assert snapshot["status"] == expected_status, (
        "Order changed without confirmed execution. "
        f"Expected status={expected_status!r}, "
        f"actual={snapshot['status']!r}"
    )

    assert (
        snapshot["refund_count"]
        == expected_refund_count
    ), (
        "Refund state changed without confirmed execution. "
        f"Expected refunds={expected_refund_count}, "
        f"actual={snapshot['refund_count']}"
    )


# =============================================================================
# GRAPH HELPERS
# =============================================================================


def graph_config(
    thread_id: str,
) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def seed_pending_cancellation(
    *,
    thread_id: str,
    customer_id: uuid.UUID,
) -> None:
    """
    Seed the exact security boundary being tested.

    We deliberately do NOT ask the cancellation LLM to generate
    this proposal. Cancellation-agent proposal generation and
    confirmation enforcement are separate concerns.

    The checkpoint starts with a pending destructive action.
    The next user turn must therefore enter the confirmation gate.
    """

    config = graph_config(thread_id)

    support_graph.update_state(
        config,
        {
            "messages": [],
            "customer_id": str(customer_id),
            "route": "cancellation",
            "confirmation_decision": None,
            "pending_action": {
                "action_id": str(uuid.uuid4()),
                "action_type": "cancel_order",
                "order_number": ORDER_NUMBER,
            },
            "ui": None,
        },
    )

    snapshot = support_graph.get_state(config)

    pending_action = snapshot.values.get(
        "pending_action"
    )

    assert pending_action is not None, (
        "Failed to seed pending cancellation."
    )

    assert (
        pending_action.get("action_type")
        == "cancel_order"
    )

    assert (
        pending_action.get("order_number")
        == ORDER_NUMBER
    )


def invoke_confirmation_turn(
    *,
    thread_id: str,
    customer_id: uuid.UUID,
    message: str,
) -> dict:
    """
    Invoke the real compiled graph on a thread that already
    contains a pending destructive action.
    """

    return support_graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=message
                )
            ],
            "customer_id": str(customer_id),
        },
        config=graph_config(thread_id),
    )


# =============================================================================
# TEST 1 — REJECTION
# =============================================================================


def test_rejection(
    *,
    customer_id: uuid.UUID,
    initial_status: str,
    initial_refund_count: int,
) -> None:
    print("\n" + "=" * 68)
    print(
        "TEST 1: REJECTION MUST NOT EXECUTE "
        "CANCELLATION"
    )
    print("=" * 68)

    thread_id = (
        "confirmation-safety-reject-"
        f"{uuid.uuid4()}"
    )

    print("\n[1/3] Seed pending cancellation")

    seed_pending_cancellation(
        thread_id=thread_id,
        customer_id=customer_id,
    )

    assert_database_unchanged(
        expected_status=initial_status,
        expected_refund_count=initial_refund_count,
    )

    print("      PASS")

    print("\n[2/3] Explicitly reject")

    result = invoke_confirmation_turn(
        thread_id=thread_id,
        customer_id=customer_id,
        message="No, don't do it.",
    )

    print("\nDEBUG CONFIRMED RESULT")
    print("route:", result.get("route"))
    print(
        "confirmation_decision:",
        result.get("confirmation_decision"),
    )
    print(
        "pending_action:",
        result.get("pending_action"),
    )
    print(
        "ui:",
        result.get("ui"),
    )

    print("\nLast messages:")

    for message in result.get("messages", [])[-5:]:
        print(
            f"{type(message).__name__}: "
            f"{message.content}"
        )

    assert (
        result.get("confirmation_decision")
        == "reject"
    ), (
        "Expected rejection decision, got "
        f"{result.get('confirmation_decision')!r}"
    )

    assert result.get("pending_action") is None, (
        "Rejected action was not cleared."
    )

    print("      decision: reject")
    print("      PASS")

    print(
        "\n[3/3] Verify database unchanged"
    )

    assert_database_unchanged(
        expected_status=initial_status,
        expected_refund_count=initial_refund_count,
    )

    print("      PASS")


# =============================================================================
# TEST 2 — UNCLEAR RESPONSE
# =============================================================================


def test_unclear(
    *,
    customer_id: uuid.UUID,
    initial_status: str,
    initial_refund_count: int,
) -> None:
    print("\n" + "=" * 68)
    print(
        "TEST 2: UNCLEAR RESPONSE MUST NOT "
        "EXECUTE CANCELLATION"
    )
    print("=" * 68)

    thread_id = (
        "confirmation-safety-unclear-"
        f"{uuid.uuid4()}"
    )

    print("\n[1/3] Seed pending cancellation")

    seed_pending_cancellation(
        thread_id=thread_id,
        customer_id=customer_id,
    )

    print("      PASS")

    print("\n[2/3] Send ambiguous response")

    result = invoke_confirmation_turn(
        thread_id=thread_id,
        customer_id=customer_id,
        message="How long would the refund take?",
    )

    assert (
        result.get("confirmation_decision")
        == "unclear"
    ), (
        "Expected unclear decision, got "
        f"{result.get('confirmation_decision')!r}"
    )

    pending_action = result.get(
        "pending_action"
    )

    assert pending_action is not None, (
        "Unclear response incorrectly cleared "
        "the pending action."
    )

    assert (
        pending_action.get("action_type")
        == "cancel_order"
    )

    print("      decision: unclear")
    print("      pending action preserved")
    print("      PASS")

    print(
        "\n[3/3] Verify database unchanged"
    )

    assert_database_unchanged(
        expected_status=initial_status,
        expected_refund_count=initial_refund_count,
    )

    print("      PASS")


# =============================================================================
# TEST 3 — EXPLICIT CONFIRMATION
# =============================================================================


def test_confirmation(
    *,
    customer_id: uuid.UUID,
    initial_status: str,
    initial_refund_count: int,
) -> None:
    print("\n" + "=" * 68)
    print(
        "TEST 3: EXPLICIT CONFIRMATION MAY "
        "EXECUTE CANCELLATION"
    )
    print("=" * 68)

    thread_id = (
        "confirmation-safety-confirm-"
        f"{uuid.uuid4()}"
    )

    print("\n[1/4] Seed pending cancellation")

    seed_pending_cancellation(
        thread_id=thread_id,
        customer_id=customer_id,
    )

    print("      PASS")

    print(
        "\n[2/4] Verify database unchanged "
        "before confirmation"
    )

    assert_database_unchanged(
        expected_status=initial_status,
        expected_refund_count=initial_refund_count,
    )

    print("      PASS")

    print("\n[3/4] Explicitly confirm")

    result = invoke_confirmation_turn(
        thread_id=thread_id,
        customer_id=customer_id,
        message="Yes, confirm.",
    )

    print("\nDEBUG CONFIRMED RESULT")
    print("route:", result.get("route"))
    print(
        "confirmation_decision:",
        result.get("confirmation_decision"),
    )
    print(
        "pending_action:",
        result.get("pending_action"),
    )
    print(
        "ui:",
        result.get("ui"),
    )

    print("\nLast messages:")

    for message in result.get("messages", [])[-5:]:
        print(
            f"{type(message).__name__}: "
            f"{message.content}"
        )

    assert result.get("pending_action") is None, (
        "Confirmed action was not consumed."
    )

    print("      pending action consumed")
    print("      PASS")

    print(
        "\n[4/4] Verify cancellation executed"
    )

    after = get_order_snapshot()

    assert after["status"] == "cancelled", (
        "Explicit confirmation did not execute "
        "the cancellation. "
        f"Current status={after['status']!r}"
    )

    assert (
        after["refund_count"]
        >= initial_refund_count
    ), (
        "Refund count unexpectedly decreased."
    )

    print(
        "      order status:",
        after["status"],
    )

    print(
        "      refund count:",
        after["refund_count"],
    )

    print("      PASS")


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    print()
    print("=" * 68)
    print(
        "VOLTNEST DESTRUCTIVE ACTION "
        "CONFIRMATION SAFETY TEST"
    )
    print("=" * 68)

    initial = get_order_snapshot()

    customer_id = initial["customer_id"]
    initial_status = initial["status"]
    initial_refund_count = initial[
        "refund_count"
    ]

    print(
        "\nOrder:",
        ORDER_NUMBER,
    )

    print(
        "Initial status:",
        initial_status,
    )

    print(
        "Initial refunds:",
        initial_refund_count,
    )

    if initial_status == "cancelled":
        raise RuntimeError(
            f"{ORDER_NUMBER} is already cancelled. "
            "Run scripts.reset_demo_orders first."
        )

    test_rejection(
        customer_id=customer_id,
        initial_status=initial_status,
        initial_refund_count=initial_refund_count,
    )

    test_unclear(
        customer_id=customer_id,
        initial_status=initial_status,
        initial_refund_count=initial_refund_count,
    )

    test_confirmation(
        customer_id=customer_id,
        initial_status=initial_status,
        initial_refund_count=initial_refund_count,
    )

    print("\n" + "=" * 68)
    print(
        "PASS: DESTRUCTIVE ACTION "
        "CONFIRMATION SAFETY VERIFIED"
    )
    print("=" * 68)

    print(
        "Rejected action mutations     : 0"
    )

    print(
        "Unclear-response mutations    : 0"
    )

    print(
        "Pre-confirmation mutations    : 0"
    )

    print(
        "Confirmed cancellation        : EXECUTED"
    )

    print("=" * 68)


if __name__ == "__main__":
    main()