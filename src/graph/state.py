from typing import (
    Annotated,
    Any,
    Literal,
)

from langchain_core.messages import (
    BaseMessage,
)
from langgraph.graph.message import (
    add_messages,
)
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


UIType = Literal[
    "order_status",
    "confirmation",
    "return_result",
    "cancellation_result",
    "support_ticket",
]


class PendingAction(
    TypedDict,
    total=False,
):
    action_id: str
    action_type: ActionType

    # Shared
    order_number: str

    # Return-specific
    order_item_id: str
    product_name: str
    quantity: int
    reason: str


class SupportUI(
    TypedDict,
):
    type: UIType
    data: dict[str, Any]


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

    # Controlled destructive/mutating
    # action state.
    pending_action: (
        PendingAction | None
    )

    # Structured presentation metadata.
    #
    # Agents/services determine facts.
    # The API/frontend use this only for
    # presentation.
    ui: SupportUI | None