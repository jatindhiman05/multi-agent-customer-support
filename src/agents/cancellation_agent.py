from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from src.tools.cancellation_tools import (
    check_order_cancellation,
)


load_dotenv()


SYSTEM_PROMPT = """
You are the VoltNest Cancellation Support Agent.

You help authenticated customers determine whether one of their
orders can be cancelled and prepare eligible cancellations for
explicit customer confirmation.

Available capabilities:
- check whether a specific order can currently be cancelled
- prepare a cancellation proposal

Rules:

1. Use the cancellation eligibility tool before proposing any
   cancellation.

2. Never invent order status, shipment status, cancellation
   eligibility, refund eligibility, or refund amounts.

3. Never ask the customer for their internal customer ID.

4. If the customer has not provided an order number, ask for it.

5. If cancellation eligibility fails, explain the reason clearly
   and DO NOT call propose_cancel_order.

6. If cancellation is eligible and the customer wants to cancel
   the order, call propose_cancel_order.

7. propose_cancel_order DOES NOT cancel the order.
   It only prepares an action requiring explicit customer
   confirmation.

8. Never claim that an order has been cancelled unless the system
   tells you the cancellation succeeded.

9. Never calculate or promise a refund amount yourself.
   Refund handling is performed by deterministic backend services
   during cancellation when applicable.

Keep responses concise and helpful.
"""


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


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
        """

        return check_order_cancellation.invoke(
            {
                "order_number": order_number,
                "customer_id": customer_id,
            }
        )

    @tool
    def propose_cancel_order(
        order_number: str,
    ) -> dict:
        """
        Prepare an order cancellation for explicit customer
        confirmation.

        This tool DOES NOT cancel the order.
        """

        return {
            "proposal_type": "cancel_order",
            "order_number": order_number,
        }

    return create_react_agent(
        model=llm,
        tools=[
            check_cancellation,
            propose_cancel_order,
        ],
        prompt=SYSTEM_PROMPT,
    )