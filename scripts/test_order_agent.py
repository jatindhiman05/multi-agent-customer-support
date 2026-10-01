from sqlalchemy import select

from langchain_core.messages import HumanMessage

from src.agents.order_agent import order_agent
from src.db.models import User
from src.db.session import SessionLocal


with SessionLocal() as session:
    customer = session.scalar(
        select(User).where(User.email == "alex@example.com")
    )

    if customer is None:
        raise RuntimeError("Seed customer not found.")

    customer_id = str(customer.id)


response = order_agent.invoke(
    {
        "messages": [
            HumanMessage(
                content=(
                    f"My customer ID is {customer_id}. "
                    "Where is my order ORD-1003?"
                )
            )
        ]
    }
)


print("\n--- FINAL RESPONSE ---")
print(response["messages"][-1].content)