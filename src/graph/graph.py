from __future__ import annotations
import uuid
import ast
from src.core.observability import observe_operation
from langchain_core.messages import (
    AIMessage,
    ToolMessage,
)
from src.agents.escalation_agent import (
    create_escalation_agent,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from src.actions.executor import (
    execute_pending_action,
)
from src.agents.cancellation_agent import (
    create_cancellation_agent,
)
from src.agents.knowledge_agent import (
    knowledge_agent,
)
from src.agents.order_agent import (
    create_order_agent,
)
from src.agents.return_agent import (
    create_return_agent,
)
from src.graph.checkpointer import checkpointer
from src.graph.confirmation import (
    classify_confirmation,
)
from src.graph.state import (
    PendingAction,
    SupportState,
)
from src.graph.supervisor import supervisor_node


# =====================================================================
# HELPERS
# =====================================================================


def _extract_tool_proposal(
    messages: list,
    *,
    tool_name: str,
) -> dict | None:
    """
    Find the most recent proposal tool result from an agent run.
    """

    for message in reversed(messages):
        if not isinstance(
            message,
            ToolMessage,
        ):
            continue

        if message.name != tool_name:
            continue

        content = message.content

        if isinstance(content, dict):
            return content

        if isinstance(content, str):
            try:
                parsed = ast.literal_eval(
                    content
                )

                if isinstance(parsed, dict):
                    return parsed

            except (
                ValueError,
                SyntaxError,
            ):
                return None

    return None


# =====================================================================
# NORMAL SPECIALIST NODES
# =====================================================================


def order_node(
    state: SupportState,
) -> dict:
    order_agent = create_order_agent(
        customer_id=state["customer_id"]
    )

    with observe_operation(
        "agent",
        agent="order",
    ):
        result = order_agent.invoke(
            {
                "messages": state["messages"],
            }
        )

    return {
        "messages": [
            result["messages"][-1]
        ],
    }


def knowledge_node(
    state: SupportState,
) -> dict:
    with observe_operation(
        "agent",
        agent="knowledge",
    ):
        result = knowledge_agent.invoke(
            {
                "messages": state["messages"],
            }
        )

    return {
        "messages": [
            result["messages"][-1]
        ],
    }

def escalation_node(
    state: SupportState,
) -> dict:
    escalation_agent = (
        create_escalation_agent(
            customer_id=state[
                "customer_id"
            ]
        )
    )

    with observe_operation(
        "agent",
        agent="escalation",
    ):
        result = escalation_agent.invoke(
            {
                "messages": state["messages"],
            }
        )

    return {
        "messages": [
            result["messages"][-1]
        ],
    }


def return_node(
    state: SupportState,
) -> dict:
    return_agent = create_return_agent(
        customer_id=state["customer_id"]
    )

    with observe_operation(
        "agent",
        agent="returns",
    ):
        result = return_agent.invoke(
            {
                "messages": state["messages"],
            }
        )

    proposal = _extract_tool_proposal(
        result["messages"],
        tool_name="propose_return_action",
    )

    if proposal is None:
        return {
            "messages": [
                result["messages"][-1]
            ],
            "pending_action": None,
        }

    required_fields = {
        "order_number",
        "order_item_id",
        "product_name",
        "quantity",
        "reason",
    }

    if not required_fields.issubset(
        proposal
    ):
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I couldn't safely prepare the return. "
                        "Please provide the return details again."
                    )
                )
            ],
            "pending_action": None,
        }

    pending_action: PendingAction = {
        "action_id": str(uuid.uuid4()),
        "action_type": "create_return",
        "order_number": proposal[
            "order_number"
        ],
        "order_item_id": proposal[
            "order_item_id"
        ],
        "product_name": proposal[
            "product_name"
        ],
        "quantity": int(
            proposal["quantity"]
        ),
        "reason": proposal[
            "reason"
        ],
    }

    return {
        "messages": [
            AIMessage(
                content=(
                    "I can create a return for "
                    f'{pending_action["quantity"]} x '
                    f'{pending_action["product_name"]} '
                    f'from order '
                    f'{pending_action["order_number"]}.\n\n'
                    f'Reason: '
                    f'{pending_action["reason"]}\n\n'
                    "Please explicitly confirm if you want "
                    "me to create this return."
                )
            )
        ],
        "pending_action": pending_action,
    }


def cancellation_node(
    state: SupportState,
) -> dict:
    cancellation_agent = (
        create_cancellation_agent(
            customer_id=state[
                "customer_id"
            ]
        )
    )

    with observe_operation(
        "agent",
        agent="cancellation",
    ):
        result = cancellation_agent.invoke(
            {
                "messages": state["messages"],
            }
        )

    proposal = _extract_tool_proposal(
        result["messages"],
        tool_name="propose_cancel_order",
    )

    # No proposal means the agent is asking for information or
    # explaining why cancellation is not allowed.
    if proposal is None:
        return {
            "messages": [
                result["messages"][-1]
            ],
            "pending_action": None,
        }

    if "order_number" not in proposal:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I couldn't safely prepare the "
                        "cancellation. Please provide the "
                        "order number again."
                    )
                )
            ],
            "pending_action": None,
        }

    pending_action: PendingAction = {
        "action_id": str(uuid.uuid4()),
        "action_type": "cancel_order",
        "order_number": proposal[
            "order_number"
        ],
    }

    return {
        "messages": [
            AIMessage(
                content=(
                    f'I can cancel order '
                    f'{pending_action["order_number"]}.\n\n'
                    "If the order has a refundable captured "
                    "payment, the backend will automatically "
                    "process the eligible refund.\n\n"
                    "Please explicitly confirm if you want "
                    "me to cancel this order."
                )
            )
        ],
        "pending_action": pending_action,
    }


# =====================================================================
# PENDING ACTION FLOW
# =====================================================================


def entry_router(
    state: SupportState,
) -> str:
    if state.get(
        "pending_action"
    ) is not None:
        return "confirmation"

    return "supervisor"


def _pending_action_description(
    action: PendingAction,
) -> str:
    action_type = action.get(
        "action_type"
    )

    if action_type == "create_return":
        return (
            f'the pending return for '
            f'{action.get("quantity")} x '
            f'{action.get("product_name")} from '
            f'{action.get("order_number")}'
        )

    if action_type == "cancel_order":
        return (
            f'the pending cancellation of order '
            f'{action.get("order_number")}'
        )

    return "the pending action"


def confirmation_node(
    state: SupportState,
) -> dict:
    with observe_operation(
        "confirmation",
    ):
        decision = classify_confirmation(
            state
        )

    if decision == "reject":
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Okay, I won't perform that action."
                    )
                )
            ],
            "pending_action": None,
            "confirmation_decision": "reject",
            "route": "confirmation",
        }

    if decision == "unclear":
        action = state["pending_action"]

        description = (
            _pending_action_description(
                action
            )
        )

        return {
            "messages": [
                AIMessage(
                    content=(
                        f"I still have {description}. "
                        "Please explicitly confirm or decline it."
                    )
                )
            ],
            "pending_action": action,
            "confirmation_decision": "unclear",
            "route": "confirmation",
        }

    return {
        "confirmation_decision": "confirm",
        "route": "confirmation",
    }


def route_confirmation(
    state: SupportState,
) -> str:
    if (
        state.get(
            "confirmation_decision"
        )
        == "confirm"
    ):
        return "execute"

    return "end"


# =====================================================================
# ACTION EXECUTION
# =====================================================================


def action_executor_node(
    state: SupportState,
) -> dict:
    action = state.get(
        "pending_action"
    )

    if action is None:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "There is no pending action."
                    )
                )
            ],
            "route": "confirmation",
        }

    action_type = action.get(
        "action_type",
        "unknown",
    )

    with observe_operation(
        "action",
        action_type=action_type,
    ):
        result = execute_pending_action(
            action=action,
            customer_id=state["customer_id"],
        )

    # -----------------------------------------------------------------
    # FAILURE
    # -----------------------------------------------------------------

    if not result["success"]:
        if action_type == "create_return":
            message = (
                "I couldn't complete the return because "
                f'{result["error"]}. '
                "No return was created."
            )

        elif action_type == "cancel_order":
            message = (
                "I couldn't cancel the order because "
                f'{result["error"]}. '
                "The order was not cancelled."
            )

        else:
            message = (
                "I couldn't complete the requested action."
            )

        return {
            "messages": [
                AIMessage(
                    content=message
                )
            ],
            "pending_action": None,
            "confirmation_decision": None,
            "route": "confirmation",
        }

    # -----------------------------------------------------------------
    # SUCCESSFUL RETURN
    # -----------------------------------------------------------------

    if action_type == "create_return":
        message = (
            "Your return has been created successfully.\n\n"
            f'Return number: {result["return_number"]}\n'
            f'Order: {result["order_number"]}\n'
            f'Item: {result["product_name"]}\n'
            f'Quantity: {result["quantity"]}\n'
            f'Status: {result["status"]}'
        )

    # -----------------------------------------------------------------
    # SUCCESSFUL CANCELLATION
    # -----------------------------------------------------------------

    elif action_type == "cancel_order":
        if result["requires_refund"]:
            message = (
                f'Order {result["order_number"]} has been '
                "cancelled successfully.\n\n"
                "An eligible refund was also created "
                "automatically."
            )

            if result.get("refund_id"):
                message += (
                    f'\nRefund ID: {result["refund_id"]}'
                )

        else:
            message = (
                f'Order {result["order_number"]} has been '
                "cancelled successfully."
            )

    else:
        message = (
            "The requested action was completed successfully."
        )

    return {
        "messages": [
            AIMessage(
                content=message
            )
        ],
        "pending_action": None,
        "confirmation_decision": None,
        "route": "confirmation",
    }

# =====================================================================
# SUPERVISOR ROUTING
# =====================================================================


def route_request(
    state: SupportState,
) -> str:
    return state["route"]


# =====================================================================
# GRAPH
# =====================================================================


def build_support_graph():
    graph = StateGraph(
        SupportState
    )

    graph.add_node(
        "supervisor",
        supervisor_node,
    )

    graph.add_node(
        "order_agent",
        order_node,
    )

    graph.add_node(
        "knowledge_agent",
        knowledge_node,
    )

    graph.add_node(
        "return_agent",
        return_node,
    )

    graph.add_node(
        "cancellation_agent",
        cancellation_node,
    )

    graph.add_node(
        "confirmation",
        confirmation_node,
    )

    graph.add_node(
        "action_executor",
        action_executor_node,
    )

    graph.add_node(
        "escalation_agent",
        escalation_node,
    )

    # -------------------------------------------------------------
    # ENTRY
    # -------------------------------------------------------------

    graph.add_conditional_edges(
        START,
        entry_router,
        {
            "supervisor": "supervisor",
            "confirmation": "confirmation",
        },
    )

    # -------------------------------------------------------------
    # SUPERVISOR ROUTING
    # -------------------------------------------------------------

    graph.add_conditional_edges(
        "supervisor",
        route_request,
        {
            "order": "order_agent",
            "knowledge": "knowledge_agent",
            "returns": "return_agent",
            "cancellation": "cancellation_agent",
            "escalation": "escalation_agent",
        },
    )

    # -------------------------------------------------------------
    # CONFIRMATION ROUTING
    # -------------------------------------------------------------

    graph.add_conditional_edges(
        "confirmation",
        route_confirmation,
        {
            "execute": "action_executor",
            "end": END,
        },
    )

    # -------------------------------------------------------------
    # TERMINAL NODES
    # -------------------------------------------------------------

    graph.add_edge(
        "order_agent",
        END,
    )

    graph.add_edge(
        "knowledge_agent",
        END,
    )

    graph.add_edge(
        "return_agent",
        END,
    )

    graph.add_edge(
        "cancellation_agent",
        END,
    )

    graph.add_edge(
        "action_executor",
        END,
    )

    graph.add_edge(
        "escalation_agent",
        END,
    )

    return graph


support_graph = (
    build_support_graph().compile(
        checkpointer=checkpointer
    )
)