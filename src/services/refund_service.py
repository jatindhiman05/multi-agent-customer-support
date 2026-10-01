from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from src.db.models import Payment, Refund
from src.repositories.payment_repository import PaymentRepository
from src.repositories.refund_repository import RefundRepository


class PaymentNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class RefundEligibility:
    allowed: bool
    reason: str
    refundable_amount: Decimal


@dataclass(frozen=True)
class RefundResult:
    created: bool
    reason: str
    refund: Refund | None


class RefundService:
    REFUNDS_CONSUMING_BALANCE = {
        "pending",
        "processing",
        "completed",
    }

    REFUNDABLE_PAYMENT_STATUSES = {
        "captured",
        "partially_refunded",
    }

    def __init__(self, session: Session):
        self.session = session
        self.payments = PaymentRepository(session)
        self.refunds = RefundRepository(session)

    def get_payment(
        self,
        payment_id: uuid.UUID,
    ) -> Payment:
        payment = self.payments.get_by_id(payment_id)

        if payment is None:
            raise PaymentNotFoundError(
                f"Payment {payment_id} was not found."
            )

        return payment

    def calculate_refundable_amount(
        self,
        payment: Payment,
    ) -> Decimal:
        existing_refunds = self.refunds.list_for_payment(
            payment.id
        )

        consumed_amount = sum(
            (
                refund.amount
                for refund in existing_refunds
                if refund.status
                in self.REFUNDS_CONSUMING_BALANCE
            ),
            Decimal("0.00"),
        )

        remaining = payment.amount - consumed_amount

        return max(
            remaining,
            Decimal("0.00"),
        )

    def check_refund_eligibility(
        self,
        *,
        payment_id: uuid.UUID,
        amount: Decimal,
    ) -> RefundEligibility:
        payment = self.get_payment(payment_id)

        refundable_amount = (
            self.calculate_refundable_amount(payment)
        )

        if payment.status not in self.REFUNDABLE_PAYMENT_STATUSES:
            return RefundEligibility(
                allowed=False,
                reason="payment_not_refundable",
                refundable_amount=refundable_amount,
            )

        if amount <= Decimal("0.00"):
            return RefundEligibility(
                allowed=False,
                reason="invalid_refund_amount",
                refundable_amount=refundable_amount,
            )

        if refundable_amount <= Decimal("0.00"):
            return RefundEligibility(
                allowed=False,
                reason="nothing_left_to_refund",
                refundable_amount=refundable_amount,
            )

        if amount > refundable_amount:
            return RefundEligibility(
                allowed=False,
                reason="amount_exceeds_refundable_balance",
                refundable_amount=refundable_amount,
            )

        return RefundEligibility(
            allowed=True,
            reason="eligible",
            refundable_amount=refundable_amount,
        )

    def create_refund(
        self,
        *,
        payment_id: uuid.UUID,
        amount: Decimal,
        reason: str,
        provider_refund_id: str | None = None,
    ) -> RefundResult:
        # ---------------------------------------------------------
        # LOCK PAYMENT
        # ---------------------------------------------------------

        payment = self.payments.get_by_id_for_update(
            payment_id
        )

        if payment is None:
            raise PaymentNotFoundError(
                f"Payment {payment_id} was not found."
            )

        # The PostgreSQL row lock remains held until this
        # transaction commits or rolls back.

        # ---------------------------------------------------------
        # CALCULATE CURRENT REFUNDABLE BALANCE
        # ---------------------------------------------------------

        refundable_amount = (
            self.calculate_refundable_amount(payment)
        )

        # ---------------------------------------------------------
        # PAYMENT STATUS
        # ---------------------------------------------------------

        if payment.status not in self.REFUNDABLE_PAYMENT_STATUSES:
            return RefundResult(
                created=False,
                reason="payment_not_refundable",
                refund=None,
            )

        # ---------------------------------------------------------
        # AMOUNT VALIDATION
        # ---------------------------------------------------------

        if amount <= Decimal("0.00"):
            return RefundResult(
                created=False,
                reason="invalid_refund_amount",
                refund=None,
            )

        if refundable_amount <= Decimal("0.00"):
            return RefundResult(
                created=False,
                reason="nothing_left_to_refund",
                refund=None,
            )

        if amount > refundable_amount:
            return RefundResult(
                created=False,
                reason="amount_exceeds_refundable_balance",
                refund=None,
            )

        # ---------------------------------------------------------
        # CREATE REFUND
        # ---------------------------------------------------------

        refund = Refund(
            payment_id=payment.id,
            return_id=None,
            provider=payment.provider,
            provider_refund_id=provider_refund_id,
            status="pending",
            amount=amount,
            currency=payment.currency,
            reason=reason,
        )

        created_refund = self.refunds.add(refund)

        return RefundResult(
            created=True,
            reason="refund_created",
            refund=created_refund,
        )