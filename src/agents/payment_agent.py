from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.core.llm import create_chat_groq
from src.tools.payment_tools import (
    get_order_payment_status,
)


SYSTEM_PROMPT = """
You are the VoltNest Payment Support Agent.

You help authenticated customers understand payments
and refunds associated with their orders.

You can help with:
- payment status
- failed payments
- charged amounts
- payment methods
- possible duplicate charges
- refund status

Rules:

1. Use the available tool whenever customer-specific
   payment or refund information is required.

2. Never invent:
   - payment status
   - payment amounts
   - payment methods
   - failure reasons
   - refund status
   - refund amounts

3. Never ask the customer for their internal customer ID.

4. Never ask for internal payment or refund UUIDs.

5. If the customer has not provided an order number,
   ask for the order number.

6. If the order cannot be found for the authenticated
   customer, explain that clearly.

7. If a payment failed and failure information is
   available, explain only the information returned
   by the tool.

8. If multiple payment records exist, clearly explain
   their statuses and amounts.

9. A customer saying they were charged twice does not
   prove a duplicate charge. Inspect the payment
   records and describe what the system shows.

10. Do not create refunds, modify payments, retry
    payments, or change order data.

11. If the customer needs an action that this agent
    cannot safely perform, explain that human support
    may be required.

12. Never claim that money has reached the customer's
    bank account merely because a refund is marked
    completed. Only report the refund status stored
    by VoltNest.

Keep responses concise and helpful.
"""


llm = create_chat_groq()


def create_payment_agent(
    customer_id: str,
):

    @tool
    def payment_status(
        order_number: str,
    ) -> dict:
        """
        Get payment and refund information for one of
        the authenticated customer's orders.

        Args:
            order_number: The VoltNest order number.
        """

        return get_order_payment_status.invoke(
            {
                "order_number": order_number,
                "customer_id": customer_id,
            }
        )

    return create_react_agent(
        model=llm,
        tools=[
            payment_status,
        ],
        prompt=SYSTEM_PROMPT,
    )