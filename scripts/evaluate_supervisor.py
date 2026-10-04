from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)

from src.graph.supervisor import supervisor_node


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    expected_route: str
    messages: list


CASES = [
    # ============================================================
    # CONVERSATION
    # ============================================================

    EvaluationCase(
        name="greeting",
        expected_route="conversation",
        messages=[
            HumanMessage(content="Hey there!")
        ],
    ),
    EvaluationCase(
        name="thanks",
        expected_route="conversation",
        messages=[
            HumanMessage(
                content="Thanks, that helped a lot."
            )
        ],
    ),
    EvaluationCase(
        name="assistant_capabilities",
        expected_route="conversation",
        messages=[
            HumanMessage(
                content="What can you help me with?"
            )
        ],
    ),

    # ============================================================
    # ORDER / DELIVERY
    # ============================================================

    EvaluationCase(
        name="order_tracking",
        expected_route="order",
        messages=[
            HumanMessage(
                content="Where is ORD-1003?"
            )
        ],
    ),
    EvaluationCase(
        name="delivery_status",
        expected_route="order",
        messages=[
            HumanMessage(
                content=(
                    "Has ORD-1003 been delivered yet?"
                )
            )
        ],
    ),
    EvaluationCase(
        name="tracking_number",
        expected_route="order",
        messages=[
            HumanMessage(
                content=(
                    "Can you give me the tracking "
                    "number for ORD-1003?"
                )
            )
        ],
    ),

    # ============================================================
    # PAYMENT
    # ============================================================

    EvaluationCase(
        name="failed_payment",
        expected_route="payment",
        messages=[
            HumanMessage(
                content=(
                    "Why did my payment fail "
                    "for ORD-1006?"
                )
            )
        ],
    ),
    EvaluationCase(
        name="charged_order",
        expected_route="payment",
        messages=[
            HumanMessage(
                content=(
                    "Was I charged for ORD-1001?"
                )
            )
        ],
    ),
    EvaluationCase(
        name="refund_money_status",
        expected_route="payment",
        messages=[
            HumanMessage(
                content=(
                    "Has the refund for ORD-1005 "
                    "reached my card yet?"
                )
            )
        ],
    ),

    # ============================================================
    # RETURNS
    # ============================================================

    EvaluationCase(
        name="return_order",
        expected_route="returns",
        messages=[
            HumanMessage(
                content=(
                    "I want to return ORD-1004."
                )
            )
        ],
    ),
    EvaluationCase(
        name="return_eligibility",
        expected_route="returns",
        messages=[
            HumanMessage(
                content=(
                    "Can I still return ORD-1001?"
                )
            )
        ],
    ),
    EvaluationCase(
        name="return_status",
        expected_route="returns",
        messages=[
            HumanMessage(
                content=(
                    "What is happening with "
                    "return RET-1004?"
                )
            )
        ],
    ),

    # ============================================================
    # CANCELLATION
    # ============================================================

    EvaluationCase(
        name="cancel_order",
        expected_route="cancellation",
        messages=[
            HumanMessage(
                content="Cancel ORD-1002."
            )
        ],
    ),
    EvaluationCase(
        name="cancellation_eligibility",
        expected_route="cancellation",
        messages=[
            HumanMessage(
                content=(
                    "Is it too late to cancel "
                    "ORD-1002?"
                )
            )
        ],
    ),

    # ============================================================
    # KNOWLEDGE / RAG
    # ============================================================

    EvaluationCase(
        name="return_policy",
        expected_route="knowledge",
        messages=[
            HumanMessage(
                content=(
                    "What is VoltNest's return policy?"
                )
            )
        ],
    ),
    EvaluationCase(
        name="warranty_policy",
        expected_route="knowledge",
        messages=[
            HumanMessage(
                content=(
                    "How long is the warranty "
                    "on your earbuds?"
                )
            )
        ],
    ),
    EvaluationCase(
        name="shipping_policy",
        expected_route="knowledge",
        messages=[
            HumanMessage(
                content=(
                    "What is your standard "
                    "shipping policy?"
                )
            )
        ],
    ),

    # ============================================================
    # ESCALATION
    # ============================================================

    EvaluationCase(
        name="human_request",
        expected_route="escalation",
        messages=[
            HumanMessage(
                content=(
                    "I want to speak to a human."
                )
            )
        ],
    ),
    EvaluationCase(
        name="explicit_escalation",
        expected_route="escalation",
        messages=[
            HumanMessage(
                content=(
                    "Please escalate this issue."
                )
            )
        ],
    ),
    EvaluationCase(
        name="human_order_investigation",
        expected_route="escalation",
        messages=[
            HumanMessage(
                content=(
                    "I need a support agent to "
                    "investigate ORD-1003."
                )
            )
        ],
    ),
    EvaluationCase(
        name="safety_concern",
        expected_route="escalation",
        messages=[
            HumanMessage(
                content=(
                    "The earbuds became extremely hot "
                    "while I was wearing them. "
                    "I need someone to investigate."
                )
            )
        ],
    ),

    # ============================================================
    # CONTEXTUAL ORDER
    # ============================================================

    EvaluationCase(
        name="context_order_delivery",
        expected_route="order",
        messages=[
            HumanMessage(
                content="Where is ORD-1003?"
            ),
            AIMessage(
                content=(
                    "ORD-1003 is currently in transit."
                )
            ),
            HumanMessage(
                content="When will it arrive?"
            ),
        ],
    ),

    # ============================================================
    # CONTEXTUAL PAYMENT
    # ============================================================

    EvaluationCase(
        name="context_payment",
        expected_route="payment",
        messages=[
            HumanMessage(
                content=(
                    "Why did my payment fail "
                    "for ORD-1006?"
                )
            ),
            AIMessage(
                content=(
                    "The payment for ORD-1006 "
                    "was declined."
                )
            ),
            HumanMessage(
                content="Was I charged?"
            ),
        ],
    ),

    # ============================================================
    # CONTEXTUAL RETURN
    # ============================================================

    EvaluationCase(
        name="context_return",
        expected_route="returns",
        messages=[
            HumanMessage(
                content=(
                    "Can I return ORD-1004?"
                )
            ),
            AIMessage(
                content=(
                    "I can help check the return "
                    "eligibility for that order."
                )
            ),
            HumanMessage(
                content=(
                    "What about the keyboard "
                    "from that order?"
                )
            ),
        ],
    ),

    # ============================================================
    # CONTEXTUAL CANCELLATION
    # ============================================================

    EvaluationCase(
        name="context_cancellation",
        expected_route="cancellation",
        messages=[
            HumanMessage(
                content=(
                    "Can I cancel ORD-1002?"
                )
            ),
            AIMessage(
                content=(
                    "I can check whether that "
                    "order is still cancellable."
                )
            ),
            HumanMessage(
                content="Yes, please do that."
            ),
        ],
    ),

    # ============================================================
    # META-CONVERSATION OVERRIDE
    # ============================================================

    EvaluationCase(
        name="meta_followup",
        expected_route="conversation",
        messages=[
            HumanMessage(
                content="Where is ORD-1003?"
            ),
            AIMessage(
                content=(
                    "ORD-1003 is currently in transit."
                )
            ),
            HumanMessage(
                content=(
                    "What do you mean by "
                    "'in transit'?"
                )
            ),
        ],
    ),

    # ============================================================
    # ESCALATION OVERRIDES OTHER ROUTES
    # ============================================================

    EvaluationCase(
        name="escalation_over_order",
        expected_route="escalation",
        messages=[
            HumanMessage(
                content=(
                    "ORD-1003 still hasn't arrived. "
                    "I want a human to investigate."
                )
            )
        ],
    ),
]


def run_case(
    case: EvaluationCase,
) -> tuple[bool, str]:
    state = {
        "messages": case.messages,
    }

    result = supervisor_node(state)

    actual_route = result["route"]

    passed = (
        actual_route == case.expected_route
    )

    return passed, actual_route


def main() -> None:
    print()
    print("=" * 72)
    print("VOLTNEST SUPERVISOR ROUTING EVALUATION")
    print("=" * 72)

    passed_count = 0
    failures = []

    for index, case in enumerate(
        CASES,
        start=1,
    ):
        try:
            passed, actual_route = run_case(
                case
            )

        except Exception as exc:
            passed = False
            actual_route = (
                f"ERROR: {type(exc).__name__}: {exc}"
            )

        if passed:
            passed_count += 1
            status = "PASS"
        else:
            status = "FAIL"

            failures.append(
                (
                    case.name,
                    case.expected_route,
                    actual_route,
                )
            )

        print(
            f"[{index:02}/{len(CASES):02}] "
            f"{status:<4} "
            f"{case.name:<28} "
            f"expected={case.expected_route:<12} "
            f"actual={actual_route}"
        )

    total = len(CASES)

    accuracy = (
        (passed_count / total) * 100
        if total
        else 0.0
    )

    print()
    print("=" * 72)
    print("RESULT")
    print("=" * 72)

    print(f"Scenarios : {total}")
    print(f"Passed    : {passed_count}")
    print(f"Failed    : {len(failures)}")
    print(f"Accuracy  : {accuracy:.1f}%")

    if failures:
        print()
        print("FAILURES")
        print("-" * 72)

        for (
            name,
            expected,
            actual,
        ) in failures:
            print(
                f"{name}: "
                f"expected={expected}, "
                f"actual={actual}"
            )

    print()
    print("=" * 72)

    if failures:
        raise SystemExit(1)

    print(
        "PASS: supervisor routing evaluation succeeded"
    )


if __name__ == "__main__":
    main()