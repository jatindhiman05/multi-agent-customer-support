from typing import Literal
from src.core.llm import create_chat_groq
from pydantic import BaseModel, Field

from src.graph.state import SupportState


class ConfirmationDecision(BaseModel):
    decision: Literal[
        "confirm",
        "reject",
        "unclear",
    ] = Field(
        description=(
            "Whether the user explicitly confirms, rejects, "
            "or gives an unclear response to the pending action."
        )
    )


llm = create_chat_groq()

confirmation_llm = llm.with_structured_output(
    ConfirmationDecision
)


SYSTEM_PROMPT = """
You classify the customer's response to a pending action.

Return:

confirm
- only when the customer clearly agrees to the proposed action
- examples: yes, confirm, do it, proceed, go ahead

reject
- when the customer clearly declines or cancels it
- examples: no, cancel that, never mind, don't do it

unclear
- questions
- changed details
- unrelated requests
- ambiguous statements
- anything that is not explicit confirmation or rejection

Do not perform the action.
Do not answer the customer.
"""


def classify_confirmation(
    state: SupportState,
) -> str:
    messages = state["messages"]

    decision = confirmation_llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            messages[-1],
        ]
    )

    return decision.decision