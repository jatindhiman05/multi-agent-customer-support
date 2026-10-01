from langchain_core.messages import HumanMessage
from sqlalchemy import text

from src.db.session import SessionLocal
from src.graph.graph import support_graph


def get_test_customer_id() -> str:
    with SessionLocal() as session:
        customer_id = session.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {
                "email": "alex@example.com",
            },
        ).scalar_one_or_none()

        if customer_id is None:
            raise RuntimeError(
                "Test customer not found."
            )

        return str(customer_id)


def run_test(
    message: str,
    customer_id: str,
):
    print("\n" + "=" * 70)
    print(f"USER: {message}")
    print("=" * 70)

    result = support_graph.invoke(
        {
            "messages": [
                HumanMessage(content=message)
            ],
            "route": None,

            # Simulates identity supplied by authentication.
            "customer_id": customer_id,
        }
    )

    print(f"\nROUTE: {result['route']}")

    print("\nASSISTANT:")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    customer_id = get_test_customer_id()

    run_test(
        message="Where is my order ORD-1003?",
        customer_id=customer_id,
    )

    run_test(
        message="How long do I have to return a VoltNest product?",
        customer_id=customer_id,
    )

    run_test(
        message="Does the VoltNest warranty cover accidental damage?",
        customer_id=customer_id,
    )