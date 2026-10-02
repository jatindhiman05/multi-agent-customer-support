from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError

from src.db.models import IdempotencyRecord
from src.db.session import SessionLocal
from src.graph.state import PendingAction
from src.repositories.idempotency_repository import (
    IdempotencyRepository,
)
from src.services.order_service import (
    OrderNotFoundError as CancellationOrderNotFoundError,
)
from src.services.order_service import OrderService
from src.services.return_service import (
    OrderNotFoundError as ReturnOrderNotFoundError,
)
from src.services.return_service import ReturnService


def _execute_create_return(
    *,
    action: PendingAction,
    customer_id: str,
) -> dict:
    try:
        customer_uuid = uuid.UUID(
            customer_id
        )

        action_id = action[
            "action_id"
        ]

        order_item_uuid = uuid.UUID(
            action["order_item_id"]
        )

        quantity = int(
            action["quantity"]
        )

        order_number = action[
            "order_number"
        ]

        product_name = action[
            "product_name"
        ]

        reason = action[
            "reason"
        ]

    except (
        ValueError,
        TypeError,
        KeyError,
    ):
        return {
            "success": False,
            "action_type": "create_return",
            "error": "invalid_action_data",
        }

    return_number = (
        f"RET-{uuid.uuid4().hex[:12].upper()}"
    )

    with SessionLocal() as session:
        idempotency = (
            IdempotencyRepository(
                session
            )
        )

        service = ReturnService(
            session
        )

        try:
            # -----------------------------------------------------
            # EXISTING COMPLETED OPERATION
            # -----------------------------------------------------

            existing = idempotency.get(
                user_id=customer_uuid,
                action_id=action_id,
            )

            if existing is not None:
                if (
                    existing.action_type
                    != "create_return"
                ):
                    session.rollback()

                    return {
                        "success": False,
                        "action_type": (
                            "create_return"
                        ),
                        "error": (
                            "idempotency_key_conflict"
                        ),
                    }

                session.rollback()

                return dict(
                    existing.result
                )

            # -----------------------------------------------------
            # BUSINESS MUTATION
            # -----------------------------------------------------

            result = service.create_return(
                order_number=order_number,
                customer_id=customer_uuid,
                order_item_id=order_item_uuid,
                quantity=quantity,
                return_number=return_number,
                reason=reason,
            )

            if not result.created:
                session.rollback()

                # Another worker may have completed this same action
                # while this transaction was waiting on the order lock.
                existing = idempotency.get(
                    user_id=customer_uuid,
                    action_id=action_id,
                )

                if existing is not None:
                    if existing.action_type != "create_return":
                        return {
                            "success": False,
                            "action_type": "create_return",
                            "error": "idempotency_key_conflict",
                        }

                    return dict(existing.result)

                return {
                    "success": False,
                    "action_type": "create_return",
                    "error": result.reason,
                }

            response = {
                "success": True,
                "action_type": "create_return",
                "return_number": (
                    result.return_request.return_number
                ),
                "status": (
                    result.return_request.status
                ),
                "order_number": order_number,
                "product_name": product_name,
                "quantity": quantity,
            }

            # -----------------------------------------------------
            # STORE IDEMPOTENT RESULT IN SAME TRANSACTION
            # -----------------------------------------------------

            record = IdempotencyRecord(
                user_id=customer_uuid,
                action_id=action_id,
                action_type="create_return",
                status="completed",
                result=response,
            )

            idempotency.add(
                record
            )

            session.commit()

            return response

        except ReturnOrderNotFoundError:
            session.rollback()

            return {
                "success": False,
                "action_type": "create_return",
                "error": "order_not_found",
            }

        except IntegrityError:
            session.rollback()

            # Another worker may have completed the same logical
            # operation concurrently. Read the winning result.
            existing = idempotency.get(
                user_id=customer_uuid,
                action_id=action_id,
            )

            if (
                existing is not None
                and existing.action_type
                == "create_return"
            ):
                return dict(
                    existing.result
                )

            raise

        except Exception:
            session.rollback()
            raise


def _execute_cancel_order(
    *,
    action: PendingAction,
    customer_id: str,
) -> dict:
    try:
        customer_uuid = uuid.UUID(
            customer_id
        )

        action_id = action[
            "action_id"
        ]

        order_number = action[
            "order_number"
        ]

    except (
        ValueError,
        TypeError,
        KeyError,
    ):
        return {
            "success": False,
            "action_type": "cancel_order",
            "error": "invalid_action_data",
        }

    with SessionLocal() as session:
        idempotency = (
            IdempotencyRepository(
                session
            )
        )

        service = OrderService(
            session
        )

        try:
            # -----------------------------------------------------
            # EXISTING COMPLETED OPERATION
            # -----------------------------------------------------

            existing = idempotency.get(
                user_id=customer_uuid,
                action_id=action_id,
            )

            if existing is not None:
                if (
                    existing.action_type
                    != "cancel_order"
                ):
                    session.rollback()

                    return {
                        "success": False,
                        "action_type": (
                            "cancel_order"
                        ),
                        "error": (
                            "idempotency_key_conflict"
                        ),
                    }

                session.rollback()

                return dict(
                    existing.result
                )

            # -----------------------------------------------------
            # BUSINESS MUTATION
            # -----------------------------------------------------

            result = service.cancel_order(
                order_number=order_number,
                customer_id=customer_uuid,
            )

            if not result.cancelled:
                session.rollback()

                # Another worker may have completed this same action
                # while this transaction was waiting on the order lock.
                existing = idempotency.get(
                    user_id=customer_uuid,
                    action_id=action_id,
                )

                if existing is not None:
                    if existing.action_type != "cancel_order":
                        return {
                            "success": False,
                            "action_type": "cancel_order",
                            "error": "idempotency_key_conflict",
                        }

                    return dict(existing.result)

                return {
                    "success": False,
                    "action_type": "cancel_order",
                    "error": result.reason,
                    "requires_refund": result.requires_refund,
                }

            response = {
                "success": True,
                "action_type": "cancel_order",
                "order_number": order_number,
                "reason": result.reason,
                "requires_refund": (
                    result.requires_refund
                ),
                "refund_id": (
                    str(result.refund_id)
                    if result.refund_id
                    else None
                ),
            }

            # The order cancellation, optional refund creation,
            # and this record all commit atomically.
            record = IdempotencyRecord(
                user_id=customer_uuid,
                action_id=action_id,
                action_type="cancel_order",
                status="completed",
                result=response,
            )

            idempotency.add(
                record
            )

            session.commit()

            return response

        except CancellationOrderNotFoundError:
            session.rollback()

            return {
                "success": False,
                "action_type": "cancel_order",
                "error": "order_not_found",
            }

        except IntegrityError:
            session.rollback()

            existing = idempotency.get(
                user_id=customer_uuid,
                action_id=action_id,
            )

            if (
                existing is not None
                and existing.action_type
                == "cancel_order"
            ):
                return dict(
                    existing.result
                )

            raise

        except Exception:
            session.rollback()
            raise


def execute_pending_action(
    *,
    action: PendingAction,
    customer_id: str,
) -> dict:
    action_type = action.get(
        "action_type"
    )

    if action_type == "create_return":
        return _execute_create_return(
            action=action,
            customer_id=customer_id,
        )

    if action_type == "cancel_order":
        return _execute_cancel_order(
            action=action,
            customer_id=customer_id,
        )

    return {
        "success": False,
        "error": "unsupported_action",
    }