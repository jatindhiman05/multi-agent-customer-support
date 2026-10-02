from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from src.core.llm import create_chat_groq
from src.tools.order_tools import (
    get_customer_order,
    get_order_tracking,
    list_customer_orders,
)

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
- If the customer asks to see, list, check, or identify their orders
  without giving a specific order number, use the my_orders tool.
- Do not ask for an order number when the customer is asking for
  their order list
- Use my_orders when the customer asks to see or identify their orders.
- Use track_order for shipment, tracking, delivery, and carrier questions.
- Use order_details when the customer asks what they purchased, which
  products are in an order, quantities, prices, totals, or payment status.
- Resolve follow-up references such as "this order", "that order",
  "this product", and "what did I buy?" using the conversation context.
- Never ask the customer for information that can be obtained from the
  available authenticated order tools..
"""

llm = create_chat_groq()


def create_order_agent(customer_id: str):

    @tool
    def track_order(order_number: str) -> dict:
        """Get shipment and tracking information for one of the authenticated
        customer's orders.

        Args:
            order_number: The VoltNest order number.
        """
        return get_order_tracking.invoke(
            {
                "order_number": order_number,
                "customer_id": customer_id,
            }
        )

    @tool
    def my_orders() -> dict:
        """List the authenticated customer's orders.

        Use this when the customer asks to see their orders,
        recent orders, latest order, or which orders they have.
        """
        return list_customer_orders.invoke(
            {
                "customer_id": customer_id,
            }
        )

    @tool
    def order_details(order_number: str) -> dict:
        """Get the authenticated customer's order details and purchased items.

        Use this when the customer asks what they ordered, which product
        is in an order, order totals, item quantities, or payment status.

        Args:
            order_number: The VoltNest order number.
        """
        return get_customer_order.invoke(
            {
                "order_number": order_number,
                "customer_id": customer_id,
            }
        )

    return create_react_agent(
        model=llm,
        tools=[
            track_order,
            my_orders,
            order_details,
        ],
        prompt=SYSTEM_PROMPT,
    )