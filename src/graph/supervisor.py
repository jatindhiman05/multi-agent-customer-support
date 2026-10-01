from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from src.graph.state import SupportState


load_dotenv()


class RouteDecision(BaseModel):
    route: Literal["order", "knowledge"] = Field(
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
   Use for questions about a customer's specific order, including:
   - order tracking
   - shipment status
   - tracking numbers
   - delivery status
   - where a specific order currently is

2. knowledge
   Use for general VoltNest information, including:
   - return policies
   - warranty policies
   - shipping policies
   - general policy questions
   - company information

Return only the appropriate route through the provided structured output.

Do not answer the customer's question yourself.
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