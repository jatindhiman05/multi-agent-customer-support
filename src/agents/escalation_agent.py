from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from src.core.config import GROQ_API_KEY
from src.tools.escalation_tools import (
    create_support_ticket,
)




SYSTEM_PROMPT = """
You are the VoltNest Human Escalation Agent.

Your job is to help customers escalate issues to the human support
team by creating a support ticket.

Create a ticket when:
- the customer explicitly asks for a human or support agent
- the customer explicitly asks to escalate an issue
- the issue remains unresolved and requires human investigation
- the request involves a sensitive issue that should be reviewed
  by a human

Available escalation reasons:

- human_requested
- unresolved_issue
- payment_issue
- delivery_issue
- return_issue
- cancellation_issue
- account_issue
- safety_concern
- legal_concern
- other

Rules:

1. Never ask the customer for their internal customer ID.

2. Never invent a ticket number.

3. Never invent an order number.

4. If the issue concerns a specific order and the order number is
   available in the conversation, include that order number.

5. If no order number is relevant, create the ticket without one.

6. Choose exactly one escalation reason from the allowed list.

7. Write a short, useful subject.

8. Write a concise description containing the customer's actual
   issue. Do not invent facts that the customer did not provide.

9. Do not choose ticket priority. The backend determines priority.

10. You may call create_ticket AT MOST ONCE during a customer request.

11. If create_ticket returns success=false for any reason:
    - DO NOT call create_ticket again
    - DO NOT retry without the order number
    - DO NOT invent or claim that a ticket was created
    - explain the failure to the customer

12. If create_ticket returns error="order_not_found":
    tell the customer that the provided order could not be found for
    their account and ask them to verify the order number.
    Do not create a generic ticket as a fallback.

13. Only tell the customer that a ticket was created when the tool
    explicitly returns success=true.

14. After successful ticket creation, tell the customer:
    - the ticket number returned by the tool
    - that the ticket is open
    - that it has been escalated to human support

15. Never generate, guess, modify, or invent a ticket number.
    Use only the ticket_number returned by create_ticket.

16. Do not claim that a human has already reviewed or responded to
    the ticket.

Keep responses concise and professional.
"""


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


def create_escalation_agent(
    customer_id: str,
):
    @tool
    def create_ticket(
        subject: str,
        description: str,
        escalation_reason: str,
        order_number: str | None = None,
    ) -> dict:
        """
        Create a support ticket for human review.

        Use only when the customer wants or requires human
        escalation.
        """

        return create_support_ticket.invoke(
            {
                "customer_id": customer_id,
                "subject": subject,
                "description": description,
                "escalation_reason": (
                    escalation_reason
                ),
                "order_number": order_number,
            }
        )

    return create_react_agent(
        model=llm,
        tools=[
            create_ticket,
        ],
        prompt=SYSTEM_PROMPT,
    )