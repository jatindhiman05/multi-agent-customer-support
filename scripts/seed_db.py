from decimal import Decimal

from sqlalchemy import select

from src.db.models import Address, Inventory, Product, User
from src.db.session import SessionLocal


SEED_CUSTOMER_EMAIL = "alex@example.com"


def seed() -> None:
    with SessionLocal() as session:
        existing_user = session.scalar(
            select(User).where(User.email == SEED_CUSTOMER_EMAIL)
        )

        if existing_user is not None:
            print("Seed data already exists. Skipping.")
            return

        customer = User(
            email=SEED_CUSTOMER_EMAIL,
            password_hash="development-only-password-hash",
            first_name="Alex",
            last_name="Morgan",
            phone="+15550001001",
            role="customer",
            status="active",
        )

        session.add(customer)
        session.flush()

        address = Address(
            user_id=customer.id,
            label="Home",
            recipient_name="Alex Morgan",
            line1="42 Market Street",
            line2=None,
            city="San Francisco",
            state="California",
            postal_code="94105",
            country_code="US",
            phone="+15550001001",
            is_default=True,
        )

        earbuds = Product(
            sku="VN-EARBUDS-001",
            name="VoltNest Wireless Earbuds",
            description="Wireless earbuds with charging case.",
            price=Decimal("79.99"),
            currency="USD",
            is_active=True,
        )

        keyboard = Product(
            sku="VN-KEYBOARD-001",
            name="VoltNest Mechanical Keyboard",
            description="Mechanical keyboard for productivity and gaming.",
            price=Decimal("119.99"),
            currency="USD",
            is_active=True,
        )

        mouse = Product(
            sku="VN-MOUSE-001",
            name="VoltNest Wireless Mouse",
            description="Ergonomic wireless mouse.",
            price=Decimal("49.99"),
            currency="USD",
            is_active=True,
        )

        session.add_all(
            [
                address,
                earbuds,
                keyboard,
                mouse,
            ]
        )

        session.flush()

        inventories = [
            Inventory(
                product_id=earbuds.id,
                quantity_on_hand=100,
                quantity_reserved=5,
            ),
            Inventory(
                product_id=keyboard.id,
                quantity_on_hand=50,
                quantity_reserved=3,
            ),
            Inventory(
                product_id=mouse.id,
                quantity_on_hand=75,
                quantity_reserved=10,
            ),
        ]

        session.add_all(inventories)

        session.commit()

        print("Foundation seed data created successfully.")


if __name__ == "__main__":
    seed()