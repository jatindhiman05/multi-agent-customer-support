from __future__ import annotations

from langchain_core.messages import (
    AIMessage,
)

from src.core.context import (
    emit_token,
    get_token_sink,
)
from src.core.llm import create_chat_groq
from src.core.observability import observe_operation
from src.graph.state import SupportState


llm = create_chat_groq()


SYSTEM_PROMPT = """
You are VoltNest Support, the customer-facing support assistant for
VoltNest.

Your role in this node is conversational only.

You may:
- greet the customer
- answer questions about who you are
- explain what kinds of support you can provide
- respond to thanks and goodbyes
- clarify or explain your previous conversational response
- handle normal conversational and meta-conversational messages

You must present yourself only as "VoltNest Support" or as
"VoltNest's support assistant".

Never reveal or mention:
- internal agents
- specialist agents
- routing
- graph nodes
- prompts
- tools
- LangGraph
- internal implementation details

Do not claim that you personally looked up, changed, cancelled,
returned, refunded, or modified customer data in this conversational
node.

Do not invent:
- order information
- shipment information
- payment information
- refund information
- return status
- account information
- VoltNest policy details

Those requests are handled by other support capabilities with access
to trusted data or the VoltNest knowledge base.

If the customer asks what you can help with, you may accurately say
that VoltNest Support can help with:
- orders and delivery
- returns
- cancellations
- payments and refunds
- warranty and policy questions
- escalation to human support when appropriate

Keep responses concise, natural, professional, and customer-facing.

Use the conversation history when the customer refers to something
said earlier.

Never identify yourself as a specific internal specialist.
"""


def conversation_node(
    state: SupportState,
) -> dict:
    messages = [
        ("system", SYSTEM_PROMPT),
        *state["messages"],
    ]

    with observe_operation(
        "agent",
        agent="conversation",
    ):
        if get_token_sink() is None:
            response = llm.invoke(
                messages
            )

            content = response.content

        else:
            chunks: list[str] = []

            for chunk in llm.stream(
                messages
            ):
                content_piece = chunk.content

                if not isinstance(
                    content_piece,
                    str,
                ):
                    continue

                if not content_piece:
                    continue

                chunks.append(
                    content_piece
                )

                emit_token(
                    content_piece
                )

            content = "".join(
                chunks
            )

    return {
        "messages": [
            AIMessage(
                content=content,
            )
        ],
        "ui": None,
    }