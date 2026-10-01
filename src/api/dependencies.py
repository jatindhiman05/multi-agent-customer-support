from sqlalchemy import text

from src.db.session import SessionLocal


def get_current_customer_id() -> str:
    """
    Temporary development authentication dependency.

    For now, this returns the seeded Alex customer.

    Later this function will be replaced by real authentication
    (for example JWT/session authentication).

    The important security boundary is that customer identity comes
    from the application, not from the user's chat message.
    """

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
                "Development customer not found."
            )

        return str(customer_id)