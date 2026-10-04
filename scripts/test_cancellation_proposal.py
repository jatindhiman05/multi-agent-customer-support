from __future__ import annotations

from langchain_core.messages import HumanMessage

from src.db.session import SessionLocal
from src.graph.graph import cancellation_node
from src.repositories.order_repository import OrderRepository


ORDER_NUMBER = "ORD-1002"


def main() -> None:
    print()
    print("=" * 68)
    print("VOLTNEST DETERMINISTIC CANCELLATION PROPOSAL TEST")
    print("=" * 68)

    # ---------------------------------------------------------
    # LOAD REAL OWNER OF THE SEEDED DEMO ORDER
    # ---------------------------------------------------------

    with SessionLocal() as session:
        repository = OrderRepository(session)

        order = repository.get_by_number(
            ORDER_NUMBER
        )

        assert order is not None, (
            f"{ORDER_NUMBER} was not found. "
            "Seed/reset the demo database first."
        )

        customer_id = str(order.user_id)
        initial_status = order.status

    print()
    print(f"Order: {ORDER_NUMBER}")
    print(f"Initial status: {initial_status}")

    assert initial_status != "cancelled", (
        f"{ORDER_NUMBER} is already cancelled. "
        "Run python -m scripts.reset_demo_orders first."
    )

    # ---------------------------------------------------------
    # REQUEST CANCELLATION
    # ---------------------------------------------------------

    print()
    print("[1/3] Request cancellation")

    state = {
        "customer_id": customer_id,
        "messages": [
            HumanMessage(
                content=f"Cancel {ORDER_NUMBER}"
            )
        ],
    }

    result = cancellation_node(state)

    pending_action = result.get(
        "pending_action"
    )

    assert pending_action is not None, (
        "Cancellation request did not create "
        "a pending action."
    )

    print("      pending action created")
    print("      PASS")

    # ---------------------------------------------------------
    # VERIFY PENDING ACTION
    # ---------------------------------------------------------

    print()
    print("[2/3] Verify pending action")

    assert (
        pending_action["action_type"]
        == "cancel_order"
    ), pending_action

    assert (
        pending_action["order_number"]
        == ORDER_NUMBER
    ), pending_action

    assert pending_action.get(
        "action_id"
    ), pending_action

    print(
        "      action_type:",
        pending_action["action_type"],
    )
    print(
        "      order_number:",
        pending_action["order_number"],
    )
    print("      PASS")

    # ---------------------------------------------------------
    # VERIFY CONFIRMATION BOUNDARY
    # ---------------------------------------------------------

    print()
    print("[3/3] Verify confirmation required")

    ui = result.get("ui")

    assert ui is not None, (
        "Confirmation UI was not created."
    )

    assert (
        ui["type"] == "confirmation"
    ), ui

    assert (
        ui["data"]["action"]
        == "cancel_order"
    ), ui

    assert (
        ui["data"]["order_number"]
        == ORDER_NUMBER
    ), ui

    # ---------------------------------------------------------
    # CRITICAL SAFETY ASSERTION
    #
    # Asking to cancel may create a PendingAction, but must not
    # mutate the actual order before explicit confirmation.
    # ---------------------------------------------------------

    with SessionLocal() as session:
        repository = OrderRepository(session)

        order = repository.get_by_number(
            ORDER_NUMBER
        )

        assert order is not None

        assert order.status == initial_status, (
            "SAFETY FAILURE: requesting cancellation "
            "mutated the order before confirmation. "
            f"Initial status={initial_status}, "
            f"current status={order.status}."
        )

        current_status = order.status

    print("      confirmation UI created")
    print(
        "      order status remains:",
        current_status,
    )
    print("      database not mutated")
    print("      PASS")

    print()
    print("=" * 68)
    print(
        "PASS: CANCELLATION REQUEST CREATED A "
        "PENDING ACTION WITHOUT MUTATING THE ORDER"
    )
    print("=" * 68)


if __name__ == "__main__":
    main()