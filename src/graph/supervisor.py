from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from src.graph.state import SupportState


load_dotenv()


class RouteDecision(BaseModel):
    route: Literal[
        "order",
        "knowledge",
        "returns",
    ] = Field(
        description="The specialist agent that should handle the request."
    )


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)

router_llm = llm.with_structured_output(RouteDecision)


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
   - "Can I return ORD-1001?"
   - checking whether an item can be returned
   - starting or discussing a return for a specific order
   - checking an existing return status
   - questions involving a specific return number

3. knowledge
   Use for general VoltNest policy or informational questions:
   - "What is your return policy?"
   - warranty policy
   - shipping policy
   - general company information

Important distinction:

General policy:
"What is your return policy?"
→ knowledge

Customer-specific:
"Can I return ORD-1001?"
→ returns

Do not answer the customer's question yourself.
Return only the route using the provided structured output.
"""


def supervisor_node(state: SupportState) -> dict:
    messages = state["messages"]

    decision = router_llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            *messages,
        ]
    )

    return {
        "route": decision.route,
    }