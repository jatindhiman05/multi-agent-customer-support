from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from src.api.main import app
from src.core.security import hash_password
from src.db.models import Order, Product, User
from src.db.models.conversation import Conversation
from src.db.session import SessionLocal


CUSTOMER_A_EMAIL = "alex@example.com"
CUSTOMER_A_PASSWORD = "VoltNestDev123!"

TEMP_CUSTOMER_EMAIL = "security-test@example.com"
TEMP_CUSTOMER_PASSWORD = "SecurityTest123!"

TEMP_ORDER_NUMBER = "ORD-SECURITY-TEST"


client = TestClient(app)


def cleanup() -> None:
    """
    Remove resources created by this security test.

    Cleanup is intentionally explicit so the normal development seed
    remains unchanged after the test.
    """

    with SessionLocal() as session:
        temp_customer = session.scalar(
            select(User).where(
                User.email == TEMP_CUSTOMER_EMAIL
            )
        )

        if temp_customer is None:
            return

        temp_order = session.scalar(
            select(Order).where(
                Order.order_number
                == TEMP_ORDER_NUMBER
            )
        )

        if temp_order is not None:
            session.delete(temp_order)

        temp_conversations = list(
            session.scalars(
                select(Conversation).where(
                    Conversation.customer_id
                    == temp_customer.id
                )
            ).all()
        )

        for conversation in temp_conversations:
            session.delete(conversation)

        session.flush()
        session.delete(temp_customer)
        session.commit()


def create_customer_b_resources() -> uuid.UUID:
    """
    Create a second customer with one order and one conversation.

    Returns the temporary conversation ID.
    """

    with SessionLocal() as session:
        existing_customer = session.scalar(
            select(User).where(
                User.email == TEMP_CUSTOMER_EMAIL
            )
        )

        if existing_customer is not None:
            raise RuntimeError(
                "Temporary security-test customer already exists. "
                "Run cleanup before retrying."
            )

        product = session.scalar(
            select(Product).where(
                Product.sku == "VN-EARBUDS-001"
            )
        )

        if product is None:
            raise RuntimeError(
                "Seeded product VN-EARBUDS-001 was not found. "
                "Run the development seed first."
            )

        customer_b = User(
            email=TEMP_CUSTOMER_EMAIL,
            password_hash=hash_password(
                TEMP_CUSTOMER_PASSWORD
            ),
            first_name="Security",
            last_name="Test",
            phone="+15559999999",
            role="customer",
            status="active",
        )

        session.add(customer_b)
        session.flush()

        order = Order(
            order_number=TEMP_ORDER_NUMBER,
            user_id=customer_b.id,
            status="processing",
            subtotal=product.price,
            shipping_amount=0,
            tax_amount=0,
            discount_amount=0,
            total_amount=product.price,
            currency="USD",
            shipping_recipient_name="Security Test",
            shipping_line1="1 Test Street",
            shipping_line2=None,
            shipping_city="Test City",
            shipping_state="California",
            shipping_postal_code="90001",
            shipping_country_code="US",
            shipping_phone="+15559999999",
        )

        session.add(order)

        conversation = Conversation(
            customer_id=customer_b.id,
            title="Private Customer B Conversation",
        )

        session.add(conversation)
        session.flush()

        conversation_id = conversation.id

        session.commit()

        return conversation_id


def login_customer_a() -> str:
    response = client.post(
        "/auth/login",
        json={
            "email": CUSTOMER_A_EMAIL,
            "password": CUSTOMER_A_PASSWORD,
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Unable to authenticate Customer A. "
            f"Status={response.status_code}, "
            f"body={response.text}"
        )

    token = response.json().get("access_token")

    if not token:
        raise RuntimeError(
            "Login response did not contain access_token."
        )

    return token


def main() -> None:
    print()
    print("=" * 60)
    print("RESOURCE AUTHORIZATION / IDOR TEST")
    print("=" * 60)

    # Make the test safe to rerun after an interrupted previous run.
    cleanup()

    try:
        conversation_b_id = (
            create_customer_b_resources()
        )

        token_a = login_customer_a()

        headers = {
            "Authorization": f"Bearer {token_a}"
        }

        print()
        print("[1/3] Customer A -> own order")

        own_order_response = client.get(
            "/orders/ORD-1001",
            headers=headers,
        )

        print(
            "      status:",
            own_order_response.status_code,
        )

        assert (
            own_order_response.status_code == 200
        ), (
            "Customer A could not access their own order."
        )

        print("      PASS")

        print()
        print(
            "[2/3] Customer A -> Customer B order"
        )

        foreign_order_response = client.get(
            f"/orders/{TEMP_ORDER_NUMBER}",
            headers=headers,
        )

        print(
            "      status:",
            foreign_order_response.status_code,
        )

        assert (
            foreign_order_response.status_code == 404
        ), (
            "IDOR vulnerability: Customer A accessed "
            "or discovered Customer B's order."
        )

        print("      PASS")

        print()
        print(
            "[3/3] Customer A -> Customer B conversation"
        )

        foreign_conversation_response = client.get(
            (
                "/conversations/"
                f"{conversation_b_id}/messages"
            ),
            headers=headers,
        )

        print(
            "      status:",
            foreign_conversation_response.status_code,
        )

        assert (
            foreign_conversation_response.status_code
            in {403, 404}
        ), (
            "IDOR vulnerability: Customer A accessed "
            "Customer B's conversation."
        )

        print("      PASS")

        print()
        print("=" * 60)
        print(
            "PASS: cross-customer resource access blocked"
        )
        print("=" * 60)

    finally:
        cleanup()

        print()
        print(
            "Temporary security-test data cleaned up."
        )


if __name__ == "__main__":
    main()