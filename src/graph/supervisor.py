from typing import Literal
from src.core.llm import create_chat_groq
from pydantic import BaseModel, Field
from src.core.logging import get_logger
from src.core.observability import observe_operation
from src.graph.state import SupportState


logger = get_logger(__name__)


class RouteDecision(BaseModel):
    route: Literal[
        "order",
        "knowledge",
        "returns",
        "cancellation",
        "escalation",
    ] = Field(
        description=(
            "The specialist agent that should handle the request."
        )
    )


llm = create_chat_groq()

router_llm = llm.with_structured_output(
    RouteDecision
)


SYSTEM_PROMPT = """
You are the routing supervisor for VoltNest customer support.

Your only job is to decide which specialist should handle the
customer's request.

Available specialists:

1. order

Use for customer-specific order and shipment questions:
- order tracking
- shipment status
- tracking numbers
- delivery status
- where an order currently is

2. returns

Use for customer-specific return operations:
- checking whether an item can be returned
- starting or discussing a return for a specific order
- checking an existing return status
- questions involving a specific return number

3. cancellation

Use for customer-specific order cancellation requests:
- cancelling an order
- checking whether an order can still be cancelled
- stopping an order before shipment

4. escalation

Use when:
- the customer explicitly asks for a human
- the customer asks for a support agent
- the customer explicitly asks to escalate an issue
- the customer says the issue remains unresolved and wants human
  review
- the customer describes a safety concern requiring human review
- the customer describes a legal concern requiring human review

Examples:

"I want to talk to a human."
-> escalation

"Please escalate this."
-> escalation

"I need a support agent to investigate ORD-1003."
-> escalation

"I have a safety concern about this product."
-> escalation

5. knowledge

Use for general VoltNest policy or informational questions:
- return policy
- warranty policy
- shipping policy
- general company information

Important distinctions:

"What is your return policy?"
-> knowledge

"Can I return ORD-1001?"
-> returns

"Can I cancel ORD-1002?"
-> cancellation

"Where is ORD-1003?"
-> order

"I want a human to investigate ORD-1003."
-> escalation

If the customer explicitly requests a human or escalation, prefer
escalation even if the issue also involves an order, return,
cancellation, payment, or delivery.

Do not answer the customer's question yourself.

Return only the route using the provided structured output.
"""


def supervisor_node(
    state: SupportState,
) -> dict:
    messages = state["messages"]

    with observe_operation(
        "supervisor",
    ):
        decision = router_llm.invoke(
            [
                ("system", SYSTEM_PROMPT),
                *messages,
            ]
        )

    logger.info(
        "route.selected",
        extra={
            "route": decision.route,
        },
    )

    return {
        "route": decision.route,
    }