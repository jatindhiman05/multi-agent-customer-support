from typing import Annotated, Literal

from langchain_core.messages import AIMessage, ToolMessage,BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


Route = Literal[
    "order",
    "knowledge",
    "returns",
    "confirmation",
]

ActionType = Literal[
    "create_return",
]


class PendingAction(TypedDict):
    action_type: ActionType
    order_number: str
    order_item_id: str
    product_name: str
    quantity: int
    reason: str


class SupportState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]

    route: Route | None

    # Trusted application context.
    customer_id: str

    confirmation_decision: Literal[
        "confirm",
        "reject",
        "unclear",
    ] | None

    # Controlled mutation state.
    pending_action: PendingAction | None