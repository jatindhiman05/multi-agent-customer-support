from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.core.llm import create_chat_groq
from src.tools.cancellation_tools import (
    check_order_cancellation,
)


SYSTEM_PROMPT = """
You are the VoltNest Cancellation Support Agent.

You help authenticated customers determine whether one of their
orders can be cancelled.

Available capability:
- check whether a specific order can currently be cancelled

Rules:

1. If the customer wants to cancel a specific order, ALWAYS call
   check_cancellation for that order before responding.

2. Never invent order status, shipment status, cancellation
   eligibility, refund eligibility, or refund amounts.

3. Never ask the customer for their internal customer ID.

4. If the customer has not provided an order number, ask for it.

5. If cancellation eligibility fails, explain the reason clearly.

6. If cancellation is eligible and the customer wants to cancel
   the order, clearly state that the order is eligible for
   cancellation.

7. You DO NOT cancel orders and you DO NOT create confirmation
   actions. The application handles confirmation and execution
   deterministically after your eligibility check.

8. Never claim that an order has been cancelled unless the system
   tells you the cancellation succeeded.

9. Never calculate or promise a refund amount yourself.

Keep responses concise and helpful.
"""


llm = create_chat_groq()


def create_cancellation_agent(
    customer_id: str,
):
    @tool
    def check_cancellation(
        order_number: str,
    ) -> dict:
        """
        Check whether one of the authenticated customer's orders
        can currently be cancelled.

        This operation is read-only.
        """

        return check_order_cancellation.invoke(
            {
                "order_number": order_number,
                "customer_id": customer_id,
            }
        )

    return create_react_agent(
        model=llm,
        tools=[
            check_cancellation,
        ],
        prompt=SYSTEM_PROMPT,
    )