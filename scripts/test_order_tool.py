from sqlalchemy import select

from src.db.models import User
from src.db.session import SessionLocal
from src.tools.order_tools import get_order_tracking


with SessionLocal() as session:
    customer = session.scalar(
        select(User).where(User.email == "alex@example.com")
    )

    if customer is None:
        raise RuntimeError("Seed customer not found.")

    customer_id = str(customer.id)


result = get_order_tracking.invoke(
    {
        "order_number": "ORD-1003",
        "customer_id": customer_id,
    }
)

print(result)