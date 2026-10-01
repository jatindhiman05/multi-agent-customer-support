from sqlalchemy import select

from src.db.models import Order
from src.db.session import SessionLocal
from src.services.shipment_service import (
    OrderNotFoundError,
    ShipmentService,
)


def main() -> None:
    with SessionLocal() as session:
        service = ShipmentService(session)

        order = session.scalar(
            select(Order).where(
                Order.order_number == "ORD-1003"
            )
        )

        if order is None:
            raise RuntimeError("ORD-1003 not found.")

        customer_id = order.user_id

        print("\n--- ORD-1003 tracking ---")

        result = service.get_order_tracking(
            order_number="ORD-1003",
            customer_id=customer_id,
        )

        print("Order:", result.order_number)
        print("Order status:", result.order_status)
        print("Shipment count:", len(result.shipments))

        for shipment in result.shipments:
            print("\nShipment")
            print(
                "Tracking number:",
                shipment.tracking_number,
            )
            print(
                "Carrier:",
                shipment.carrier,
            )
            print(
                "Status:",
                shipment.status,
            )
            print(
                "Estimated delivery:",
                shipment.estimated_delivery_at,
            )

            print("Tracking events:")

            for event in shipment.events:
                print(
                    "-",
                    event.occurred_at,
                    event.status,
                    event.location,
                    event.description,
                )

        # -----------------------------------------------------
        # ORDER WITH NO SHIPMENT
        # -----------------------------------------------------

        print("\n--- ORD-1002 tracking ---")

        result = service.get_order_tracking(
            order_number="ORD-1002",
            customer_id=customer_id,
        )

        print("Order:", result.order_number)
        print("Order status:", result.order_status)
        print(
            "Shipment count:",
            len(result.shipments),
        )

        # -----------------------------------------------------
        # OWNERSHIP ISOLATION
        # -----------------------------------------------------

        print("\n--- Ownership isolation ---")

        fake_customer_id = (
            customer_id.__class__(
                "00000000-0000-0000-0000-000000000001"
            )
        )

        try:
            service.get_order_tracking(
                order_number="ORD-1003",
                customer_id=fake_customer_id,
            )

            print("ERROR: ownership check failed")

        except OrderNotFoundError:
            print("Access blocked")


if __name__ == "__main__":
    main()