from typing import Annotated, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


Route = Literal[
    "order",
    "knowledge",
    "returns",
    "cancellation",
    "escalation",
    "confirmation",
]


ActionType = Literal[
    "create_return",
    "cancel_order",
]


class PendingAction(
    TypedDict,
    total=False,
):
    action_type: ActionType

    # Shared
    order_number: str

    # Return-specific
    order_item_id: str
    product_name: str
    quantity: int
    reason: str


class SupportState(
    TypedDict,
    total=False,
):
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    route: Route | None

    # Trusted application context.
    customer_id: str

    confirmation_decision: Literal[
        "confirm",
        "reject",
        "unclear",
    ] | None

    # Controlled destructive/mutating action state.
    pending_action: PendingAction | None