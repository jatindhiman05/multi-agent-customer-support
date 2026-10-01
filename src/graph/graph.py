from langgraph.graph import END, START, StateGraph

from src.agents.knowledge_agent import knowledge_agent
from src.agents.order_agent import create_order_agent
from src.graph.state import SupportState
from src.graph.supervisor import supervisor_node


def order_node(state: SupportState) -> dict:
    customer_id = state["customer_id"]

    order_agent = create_order_agent(
        customer_id=customer_id
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


def route_request(state: SupportState) -> str:
    return state["route"]


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

    graph.add_edge(
        START,
        "supervisor",
    )

    graph.add_conditional_edges(
        "supervisor",
        route_request,
        {
            "order": "order_agent",
            "knowledge": "knowledge_agent",
        },
    )

    graph.add_edge(
        "order_agent",
        END,
    )

    graph.add_edge(
        "knowledge_agent",
        END,
    )

    return graph.compile()


support_graph = build_support_graph()