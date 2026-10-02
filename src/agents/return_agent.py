from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from src.core.config import GROQ_API_KEY
from src.tools.return_tools import (
    check_return_eligibility,
    get_return_status,
    get_returnable_order_items,
)




SYSTEM_PROMPT = """
You are the VoltNest Returns Support Agent.

You handle customer-specific return requests and return status questions.

Available capabilities:
- find items in a customer's order
- check return eligibility
- check existing return status
- prepare a return proposal for explicit customer confirmation

Rules:

1. Use tools whenever customer-specific information is required.

2. Never invent:
   - order items
   - return eligibility
   - quantities
   - return numbers
   - return statuses

3. Never ask for the customer's internal customer ID.

4. Never ask the customer for an internal order-item UUID.

5. If the customer identifies an order but not its internal item ID,
   use list_order_items.

6. If multiple products exist and the requested product is ambiguous,
   ask which product they mean.

7. Before proposing a return you MUST know:
   - order number
   - exact order item
   - product name
   - quantity
   - customer's reason
   - confirmed eligibility for that quantity

8. If information is missing, ask for only the missing information.

9. If eligibility fails, explain that result and DO NOT call
   propose_return_action.

10. If all required information is known and eligibility is confirmed,
    call propose_return_action.

11. propose_return_action DOES NOT create the return. It only prepares
    a proposal requiring explicit customer confirmation.

12. Never claim a return was created unless the system tells you it was.

Keep responses concise.
"""


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


def create_return_agent(customer_id: str):

    @tool
    def list_order_items(order_number: str) -> dict:
        """Get items from the authenticated customer's order."""

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
        """Check whether an order item quantity can be returned."""

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
        """Get an existing return belonging to this customer."""

        return get_return_status.invoke(
            {
                "return_number": return_number,
                "customer_id": customer_id,
            }
        )

    @tool
    def propose_return_action(
        order_number: str,
        order_item_id: str,
        product_name: str,
        quantity: int,
        reason: str,
    ) -> dict:
        """
        Prepare a return action for explicit customer confirmation.

        Call this only after return eligibility has been verified.

        This tool DOES NOT create the return.
        """

        return {
            "proposal_type": "create_return",
            "order_number": order_number,
            "order_item_id": order_item_id,
            "product_name": product_name,
            "quantity": quantity,
            "reason": reason,
        }

    return create_react_agent(
        model=llm,
        tools=[
            list_order_items,
            check_item_return_eligibility,
            lookup_return,
            propose_return_action,
        ],
        prompt=SYSTEM_PROMPT,
    )