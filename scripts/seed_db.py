from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from src.core.security import hash_password
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import (
    Address,
    Inventory,
    Order,
    OrderItem,
    Payment,
    Product,
    Refund,
    ReturnItem,
    ReturnRequest,
    Shipment,
    ShipmentItem,
    SupportTicket,
    TrackingEvent,
    User,
)
from src.db.session import SessionLocal


CUSTOMER_EMAIL = "alex@example.com"
AGENT_EMAIL = "maya.agent@voltnest.example"


def get_user(session: Session, email: str) -> User | None:
    return session.scalar(
        select(User).where(User.email == email)
    )


def get_product(session: Session, sku: str) -> Product | None:
    return session.scalar(
        select(Product).where(Product.sku == sku)
    )


def get_order(session: Session, order_number: str) -> Order | None:
    return session.scalar(
        select(Order).where(Order.order_number == order_number)
    )


def seed_users(session: Session) -> tuple[User, User]:
    customer = get_user(session, CUSTOMER_EMAIL)

    if customer is None:
        customer = User(
            email=CUSTOMER_EMAIL,
            password_hash=hash_password(
                "VoltNestDev123!"
            ),
            first_name="Alex",
            last_name="Morgan",
            phone="+15550001001",
            role="customer",
            status="active",
        )
        session.add(customer)

    agent = get_user(session, AGENT_EMAIL)

    if agent is None:
        agent = User(
            email=AGENT_EMAIL,
            password_hash="development-only-password-hash",
            first_name="Maya",
            last_name="Patel",
            phone="+15550002001",
            role="support_agent",
            status="active",
        )
        session.add(agent)

    session.flush()

    return customer, agent


def seed_address(session: Session, customer: User) -> None:
    existing = session.scalar(
        select(Address).where(
            Address.user_id == customer.id,
            Address.label == "Home",
        )
    )

    if existing is not None:
        return

    session.add(
        Address(
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
    )


def seed_products(session: Session) -> dict[str, Product]:
    definitions = [
        {
            "sku": "VN-EARBUDS-001",
            "name": "VoltNest Wireless Earbuds",
            "description": "Wireless earbuds with charging case.",
            "price": Decimal("79.99"),
            "quantity_on_hand": 100,
            "quantity_reserved": 5,
        },
        {
            "sku": "VN-KEYBOARD-001",
            "name": "VoltNest Mechanical Keyboard",
            "description": "Mechanical keyboard for productivity and gaming.",
            "price": Decimal("119.99"),
            "quantity_on_hand": 50,
            "quantity_reserved": 3,
        },
        {
            "sku": "VN-MOUSE-001",
            "name": "VoltNest Wireless Mouse",
            "description": "Ergonomic wireless mouse.",
            "price": Decimal("49.99"),
            "quantity_on_hand": 75,
            "quantity_reserved": 10,
        },
    ]

    products: dict[str, Product] = {}

    for definition in definitions:
        product = get_product(session, definition["sku"])

        if product is None:
            product = Product(
                sku=definition["sku"],
                name=definition["name"],
                description=definition["description"],
                price=definition["price"],
                currency="USD",
                is_active=True,
            )
            session.add(product)
            session.flush()

        inventory = session.scalar(
            select(Inventory).where(
                Inventory.product_id == product.id
            )
        )

        if inventory is None:
            session.add(
                Inventory(
                    product_id=product.id,
                    quantity_on_hand=definition["quantity_on_hand"],
                    quantity_reserved=definition["quantity_reserved"],
                )
            )

        products[definition["sku"]] = product

    return products


def create_order(
    session: Session,
    customer: User,
    product: Product,
    *,
    order_number: str,
    status: str,
    quantity: int = 1,
) -> Order:
    existing = get_order(session, order_number)

    if existing is not None:
        return existing

    subtotal = product.price * quantity
    shipping = Decimal("5.00")
    tax = (subtotal * Decimal("0.08")).quantize(Decimal("0.01"))
    discount = Decimal("0.00")
    total = subtotal + shipping + tax - discount

    order = Order(
        order_number=order_number,
        user_id=customer.id,
        status=status,
        subtotal=subtotal,
        shipping_amount=shipping,
        tax_amount=tax,
        discount_amount=discount,
        total_amount=total,
        currency="USD",
        shipping_recipient_name="Alex Morgan",
        shipping_line1="42 Market Street",
        shipping_line2=None,
        shipping_city="San Francisco",
        shipping_state="California",
        shipping_postal_code="94105",
        shipping_country_code="US",
        shipping_phone="+15550001001",
    )

    session.add(order)
    session.flush()

    session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            sku=product.sku,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.price,
            line_total=subtotal,
        )
    )

    session.flush()

    return order


def seed_orders(
    session: Session,
    customer: User,
    products: dict[str, Product],
) -> dict[str, Order]:
    definitions = [
        ("ORD-1001", "delivered", "VN-EARBUDS-001"),
        ("ORD-1002", "processing", "VN-KEYBOARD-001"),
        ("ORD-1003", "shipped", "VN-MOUSE-001"),
        ("ORD-1004", "delivered", "VN-KEYBOARD-001"),
        ("ORD-1005", "delivered", "VN-EARBUDS-001"),
        ("ORD-1006", "pending", "VN-MOUSE-001"),
    ]

    orders: dict[str, Order] = {}

    for order_number, status, sku in definitions:
        orders[order_number] = create_order(
            session,
            customer,
            products[sku],
            order_number=order_number,
            status=status,
        )

    return orders


def seed_payments(
    session: Session,
    orders: dict[str, Order],
) -> dict[str, Payment]:
    payments: dict[str, Payment] = {}

    for order_number, order in orders.items():
        transaction_id = f"txn_{order_number.lower().replace('-', '_')}"

        payment = session.scalar(
            select(Payment).where(
                Payment.provider == "stripe",
                Payment.provider_transaction_id == transaction_id,
            )
        )

        if payment is None:
            failed = order_number == "ORD-1006"

            payment = Payment(
                order_id=order.id,
                provider="stripe",
                provider_transaction_id=transaction_id,
                payment_method="card",
                status="failed" if failed else "captured",
                amount=order.total_amount,
                currency=order.currency,
                failure_code="card_declined" if failed else None,
                failure_message=(
                    "The card was declined by the issuer."
                    if failed
                    else None
                ),
            )

            session.add(payment)
            session.flush()

        payments[order_number] = payment

    return payments


def seed_shipment(
    session: Session,
    order: Order,
    *,
    tracking_number: str,
    status: str,
    shipped_days_ago: int,
    delivered_days_ago: int | None = None,
) -> Shipment:
    shipment = session.scalar(
        select(Shipment).where(
            Shipment.tracking_number == tracking_number
        )
    )

    if shipment is not None:
        return shipment

    now = datetime.now(timezone.utc)

    shipment = Shipment(
        order_id=order.id,
        carrier="VoltShip",
        tracking_number=tracking_number,
        status=status,
        shipped_at=now - timedelta(days=shipped_days_ago),
        estimated_delivery_at=now + timedelta(days=2),
        delivered_at=(
            now - timedelta(days=delivered_days_ago)
            if delivered_days_ago is not None
            else None
        ),
    )

    session.add(shipment)
    session.flush()

    order_item = session.scalar(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )

    if order_item is None:
        raise RuntimeError(
            f"Order {order.order_number} has no order item."
        )

    session.add(
        ShipmentItem(
            shipment_id=shipment.id,
            order_item_id=order_item.id,
            quantity=order_item.quantity,
        )
    )

    session.flush()

    return shipment


def seed_tracking_event(
    session: Session,
    shipment: Shipment,
    *,
    status: str,
    description: str,
    location: str,
    occurred_at: datetime,
) -> None:
    existing = session.scalar(
        select(TrackingEvent).where(
            TrackingEvent.shipment_id == shipment.id,
            TrackingEvent.status == status,
            TrackingEvent.occurred_at == occurred_at,
        )
    )

    if existing is not None:
        return

    session.add(
        TrackingEvent(
            shipment_id=shipment.id,
            status=status,
            description=description,
            location=location,
            occurred_at=occurred_at,
        )
    )


def seed_shipments(
    session: Session,
    orders: dict[str, Order],
) -> None:
    now = datetime(
        2026,
        10,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    delivered = seed_shipment(
        session,
        orders["ORD-1001"],
        tracking_number="VS1000001",
        status="delivered",
        shipped_days_ago=7,
        delivered_days_ago=4,
    )

    seed_tracking_event(
        session,
        delivered,
        status="shipped",
        description="Package departed the fulfillment center.",
        location="San Jose, CA",
        occurred_at=now - timedelta(days=7),
    )

    seed_tracking_event(
        session,
        delivered,
        status="in_transit",
        description="Package is moving through the carrier network.",
        location="Oakland, CA",
        occurred_at=now - timedelta(days=6),
    )

    seed_tracking_event(
        session,
        delivered,
        status="delivered",
        description="Package delivered successfully.",
        location="San Francisco, CA",
        occurred_at=now - timedelta(days=4),
    )

    in_transit = seed_shipment(
        session,
        orders["ORD-1003"],
        tracking_number="VS1000003",
        status="in_transit",
        shipped_days_ago=2,
    )

    seed_tracking_event(
        session,
        in_transit,
        status="shipped",
        description="Package departed the fulfillment center.",
        location="San Jose, CA",
        occurred_at=now - timedelta(days=2),
    )

    seed_tracking_event(
        session,
        in_transit,
        status="in_transit",
        description="Package arrived at regional sorting facility.",
        location="Oakland, CA",
        occurred_at=now - timedelta(days=1),
    )

    # Delivered orders used by return/refund scenarios.
    seed_shipment(
        session,
        orders["ORD-1004"],
        tracking_number="VS1000004",
        status="delivered",
        shipped_days_ago=10,
        delivered_days_ago=7,
    )

    seed_shipment(
        session,
        orders["ORD-1005"],
        tracking_number="VS1000005",
        status="delivered",
        shipped_days_ago=14,
        delivered_days_ago=11,
    )


def seed_return(
    session: Session,
    customer: User,
    order: Order,
    *,
    return_number: str,
    status: str,
    reason: str,
) -> ReturnRequest:
    existing = session.scalar(
        select(ReturnRequest).where(
            ReturnRequest.return_number == return_number
        )
    )

    if existing is not None:
        return existing

    now = datetime.now(timezone.utc)

    return_request = ReturnRequest(
        return_number=return_number,
        order_id=order.id,
        user_id=customer.id,
        status=status,
        reason=reason,
        customer_notes="Seeded development return.",
        requested_at=now - timedelta(days=2),
        received_at=(
            now - timedelta(days=1)
            if status == "completed"
            else None
        ),
        completed_at=(
            now
            if status == "completed"
            else None
        ),
    )

    session.add(return_request)
    session.flush()

    order_item = session.scalar(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )

    if order_item is None:
        raise RuntimeError(
            f"Order {order.order_number} has no order item."
        )

    session.add(
        ReturnItem(
            return_id=return_request.id,
            order_item_id=order_item.id,
            quantity=1,
        )
    )

    session.flush()

    return return_request


def seed_returns_and_refunds(
    session: Session,
    customer: User,
    orders: dict[str, Order],
    payments: dict[str, Payment],
) -> None:
    seed_return(
        session,
        customer,
        orders["ORD-1004"],
        return_number="RET-1004",
        status="requested",
        reason="Keyboard does not meet expectations.",
    )

    completed_return = seed_return(
        session,
        customer,
        orders["ORD-1005"],
        return_number="RET-1005",
        status="completed",
        reason="Earbuds were defective.",
    )

    refund = session.scalar(
        select(Refund).where(
            Refund.provider == "stripe",
            Refund.provider_refund_id == "refund_ord_1005",
        )
    )

    if refund is None:
        payment = payments["ORD-1005"]

        refund = Refund(
            payment_id=payment.id,
            return_id=completed_return.id,
            provider="stripe",
            provider_refund_id="refund_ord_1005",
            status="completed",
            amount=payment.amount,
            currency=payment.currency,
            reason="Returned defective product.",
            failure_code=None,
            failure_message=None,
        )

        session.add(refund)


def seed_support_tickets(
    session: Session,
    customer: User,
    agent: User,
    orders: dict[str, Order],
) -> None:
    ticket = session.scalar(
        select(SupportTicket).where(
            SupportTicket.ticket_number == "TKT-1001"
        )
    )

    if ticket is None:
        session.add(
            SupportTicket(
                ticket_number="TKT-1001",
                user_id=customer.id,
                order_id=orders["ORD-1003"].id,
                assigned_to=None,
                subject="Package has not arrived yet",
                description=(
                    "Customer wants an update on the shipment "
                    "for ORD-1003."
                ),
                status="open",
                priority="normal",
                escalation_reason="Customer requested human assistance.",
                resolved_at=None,
            )
        )

    ticket = session.scalar(
        select(SupportTicket).where(
            SupportTicket.ticket_number == "TKT-1002"
        )
    )

    if ticket is None:
        session.add(
            SupportTicket(
                ticket_number="TKT-1002",
                user_id=customer.id,
                order_id=orders["ORD-1006"].id,
                assigned_to=agent.id,
                subject="Payment repeatedly declined",
                description=(
                    "Customer needs assistance understanding "
                    "the failed payment."
                ),
                status="in_progress",
                priority="high",
                escalation_reason="Payment issue requires human review.",
                resolved_at=None,
            )
        )


def seed() -> None:
    with SessionLocal() as session:
        try:
            customer, agent = seed_users(session)

            seed_address(session, customer)

            products = seed_products(session)

            orders = seed_orders(
                session,
                customer,
                products,
            )

            payments = seed_payments(
                session,
                orders,
            )

            seed_shipments(
                session,
                orders,
            )

            seed_returns_and_refunds(
                session,
                customer,
                orders,
                payments,
            )

            seed_support_tickets(
                session,
                customer,
                agent,
                orders,
            )

            session.commit()

            print("Development seed data synchronized successfully.")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    seed()