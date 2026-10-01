from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from src.tools.order_tools import get_order_tracking


load_dotenv()


SYSTEM_PROMPT = """
You are the VoltNest Order Support Agent.

You help customers with their specific orders and shipments.

Rules:
- Use the available tools whenever real order information is required.
- Never invent order status, tracking numbers, carriers, delivery dates,
  shipment events, or company procedures.
- Answer only using information returned by the tools.
- Never ask the customer for their internal customer ID.
- If the order cannot be found, explain that clearly.
- Keep responses concise and helpful.
"""


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


def create_order_agent(customer_id: str):

    @tool
    def track_order(order_number: str) -> dict:
        """
        Get shipment and tracking information for one of the
        authenticated customer's orders.

        Args:
            order_number: The VoltNest order number.
        """

        return get_order_tracking.invoke(
            {
                "order_number": order_number,
                "customer_id": customer_id,
            }
        )

    return create_react_agent(
        model=llm,
        tools=[track_order],
        prompt=SYSTEM_PROMPT,
    )