from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from src.tools.return_tools import (
    check_return_eligibility,
    get_return_status,
    get_returnable_order_items,
)


load_dotenv()


SYSTEM_PROMPT = """
You are the VoltNest Returns Support Agent.

You handle customer-specific return requests and return status questions.

You have tools for:
- finding items in a customer's order
- checking whether an item quantity is returnable
- checking the status of an existing return

Rules:

1. Use tools whenever customer-specific order or return information
   is required.

2. Never invent:
   - order items
   - return eligibility
   - return quantities
   - return numbers
   - return statuses

3. Never ask the customer for their internal customer ID.

4. If the customer provides an order number but not an internal
   order item ID, use the order-items tool to discover the items.

5. Internal UUIDs are implementation details. Do not ask customers
   to provide UUIDs and do not expose them unless necessary.

6. If the order contains multiple items and it is unclear which item
   the customer wants to return, ask them to identify the product.

7. If the customer asks to start a return, first determine the item,
   quantity, and eligibility.

8. You are currently not authorized to create or modify returns.
   Explain eligibility and gather the necessary information, but do
   not claim that a return has been created.

9. Keep responses concise and helpful.
"""


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


def create_return_agent(customer_id: str):

    @tool
    def list_order_items(order_number: str) -> dict:
        """
        Get items from one of the authenticated customer's orders.
        """

        return get_returnable_order_items.invoke(
            {
                "order_number": order_number,
                "customer_id": customer_id,
            }
        )

    @tool
    def check_item_return_eligibility(
        order_number: str,
        order_item_id: str,
        quantity: int = 1,
    ) -> dict:
        """
        Check whether an item from the authenticated customer's
        order can be returned.
        """

        return check_return_eligibility.invoke(
            {
                "order_number": order_number,
                "order_item_id": order_item_id,
                "quantity": quantity,
                "customer_id": customer_id,
            }
        )

    @tool
    def lookup_return(return_number: str) -> dict:
        """
        Get an existing return belonging to the authenticated customer.
        """

        return get_return_status.invoke(
            {
                "return_number": return_number,
                "customer_id": customer_id,
            }
        )

    return create_react_agent(
        model=llm,
        tools=[
            list_order_items,
            check_item_return_eligibility,
            lookup_return,
        ],
        prompt=SYSTEM_PROMPT,
    )