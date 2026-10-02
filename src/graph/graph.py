from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from src.actions.executor import execute_pending_action
from src.agents.knowledge_agent import knowledge_agent
from src.agents.order_agent import create_order_agent
from src.agents.return_agent import create_return_agent
from src.graph.checkpointer import checkpointer
from src.graph.confirmation import classify_confirmation
from src.graph.state import PendingAction, SupportState
from src.graph.supervisor import supervisor_node


# ============================================================
# NORMAL SPECIALIST NODES
# ============================================================


def order_node(state: SupportState) -> dict:
    order_agent = create_order_agent(
        customer_id=state["customer_id"]
    )

    result = order_agent.invoke(
        {
            "messages": state["messages"],
        }
    )

    return {
        "messages": [result["messages"][-1]],
    }


def knowledge_node(state: SupportState) -> dict:
    result = knowledge_agent.invoke(
        {
            "messages": state["messages"],
        }
    )

    return {
        "messages": [result["messages"][-1]],
    }

def return_node(state: SupportState) -> dict:
    return_agent = create_return_agent(
        customer_id=state["customer_id"]
    )

    result = return_agent.invoke(
        {
            "messages": state["messages"],
        }
    )

    proposal = None

    for message in reversed(result["messages"]):
        if not isinstance(message, ToolMessage):
            continue

        if message.name != "propose_return_action":
            continue

        content = message.content

        # LangChain tool messages may contain the returned dict
        # directly or a serialized representation depending on version.
        if isinstance(content, dict):
            proposal = content
        else:
            import ast

            try:
                parsed = ast.literal_eval(content)

                if isinstance(parsed, dict):
                    proposal = parsed
            except (ValueError, SyntaxError):
                proposal = None

        break

    # ---------------------------------------------------------
    # No mutation proposal -> ordinary Returns Agent response
    # ---------------------------------------------------------

    if proposal is None:
        return {
            "messages": [
                result["messages"][-1]
            ],
            "pending_action": None,
        }

    # ---------------------------------------------------------
    # Validate proposal
    # ---------------------------------------------------------

    required_fields = {
        "order_number",
        "order_item_id",
        "product_name",
        "quantity",
        "reason",
    }

    if not required_fields.issubset(proposal):
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
        "action_type": "create_return",
        "order_number": proposal["order_number"],
        "order_item_id": proposal["order_item_id"],
        "product_name": proposal["product_name"],
        "quantity": int(proposal["quantity"]),
        "reason": proposal["reason"],
    }

    return {
        "messages": [
            AIMessage(
                content=(
                    f'I can create a return for '
                    f'{pending_action["quantity"]} × '
                    f'{pending_action["product_name"]} '
                    f'from order '
                    f'{pending_action["order_number"]}.\n\n'
                    f'Reason: '
                    f'{pending_action["reason"]}\n\n'
                    f'Please explicitly confirm if you want '
                    f'me to create this return.'
                )
            )
        ],
        "pending_action": pending_action,
    }

# ============================================================
# PENDING ACTION FLOW
# ============================================================


def entry_router(state: SupportState) -> str:
    if state.get("pending_action") is not None:
        return "confirmation"

    return "supervisor"

def confirmation_node(state: SupportState) -> dict:
    decision = classify_confirmation(state)

    if decision == "reject":
        return {
            "messages": [
                AIMessage(
                    content="Okay, I won't perform that action."
                )
            ],
            "pending_action": None,
            "confirmation_decision": "reject",
            "route": "confirmation",
        }

    if decision == "unclear":
        action = state["pending_action"]

        return {
            "messages": [
                AIMessage(
                    content=(
                        "I still have the pending return for "
                        f'{action["quantity"]} x '
                        f'{action["product_name"]} from '
                        f'{action["order_number"]}. '
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
    }

def route_confirmation(state: SupportState) -> str:
    if state.get("confirmation_decision") == "confirm":
        return "execute"

    return "end"


def action_executor_node(
    state: SupportState,
) -> dict:

    action = state.get("pending_action")

    if action is None:
        return {
            "messages": [
                AIMessage(
                    content="There is no pending action."
                )
            ]
        }

    result = execute_pending_action(
        action=action,
        customer_id=state["customer_id"],
    )

    if not result["success"]:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I couldn't complete the return because "
                        f'{result["error"]}. No return was created.'
                    )
                )
            ],
            "pending_action": None,
        }

    return {
        "messages": [
            AIMessage(
                content=(
                    "Your return has been created successfully.\n\n"
                    f'Return number: {result["return_number"]}\n'
                    f'Order: {result["order_number"]}\n'
                    f'Item: {result["product_name"]}\n'
                    f'Quantity: {result["quantity"]}\n'
                    f'Status: {result["status"]}'
                )
            )
        ],
        "pending_action": None,
        "confirmation_decision": None,
    }


# ============================================================
# SUPERVISOR ROUTING
# ============================================================


def route_request(state: SupportState) -> str:
    return state["route"]


# ============================================================
# GRAPH
# ============================================================


def build_support_graph():
    graph = StateGraph(SupportState)

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
        "confirmation",
        confirmation_node,
    )

    graph.add_node(
        "action_executor",
        action_executor_node,
    )

    # --------------------------------------------------------
    # ENTRY
    # --------------------------------------------------------

    graph.add_conditional_edges(
        START,
        entry_router,
        {
            "supervisor": "supervisor",
            "confirmation": "confirmation",
        },
    )

    # --------------------------------------------------------
    # NORMAL ROUTING
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "supervisor",
        route_request,
        {
            "order": "order_agent",
            "knowledge": "knowledge_agent",
            "returns": "return_agent",
        },
    )

    # --------------------------------------------------------
    # CONFIRMATION ROUTING
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "confirmation",
        route_confirmation,
        {
            "execute": "action_executor",
            "end": END,
        },
    )

    # --------------------------------------------------------
    # TERMINAL NODES
    # --------------------------------------------------------

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
        "action_executor",
        END,
    )

    return graph


support_graph = build_support_graph().compile(
    checkpointer=checkpointer
)