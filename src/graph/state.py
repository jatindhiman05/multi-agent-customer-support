from typing import Annotated, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


Route = Literal["order", "knowledge"]


class SupportState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # Set by the supervisor.
    route: Route | None

    # Trusted application context.
    # Eventually populated from authentication, never from user text.
    customer_id: str