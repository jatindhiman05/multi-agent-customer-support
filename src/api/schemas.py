import uuid
from typing import Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
    )

    conversation_id: uuid.UUID | None = None

class SupportUIResponse(BaseModel):
    type: Literal[
        "order_status",
        "order_list",
        "order_details",
        "payment_status",
        "confirmation",
        "return_result",
        "cancellation_result",
        "support_ticket",
    ]

    data: dict[str, Any]

class ChatResponse(BaseModel):
    response: str
    route: str
    conversation_id: uuid.UUID
    ui: SupportUIResponse | None = None


class LoginRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=255,
    )

    password: str = Field(
        min_length=8,
        max_length=256,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str

class OrderSummaryResponse(BaseModel):
    order_number: str
    status: str
    total_amount: Decimal
    currency: str
    created_at: datetime


class OrderItemResponse(BaseModel):
    sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class ShipmentResponse(BaseModel):
    carrier: str | None
    tracking_number: str | None
    status: str
    shipped_at: datetime | None
    estimated_delivery_at: datetime | None
    delivered_at: datetime | None


class PaymentResponse(BaseModel):
    provider: str
    payment_method: str
    status: str
    amount: Decimal
    currency: str


class OrderDetailResponse(BaseModel):
    order_number: str
    status: str

    subtotal: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str

    shipping_recipient_name: str
    shipping_line1: str
    shipping_line2: str | None
    shipping_city: str
    shipping_state: str
    shipping_postal_code: str
    shipping_country_code: str

    created_at: datetime
    updated_at: datetime

    items: list[OrderItemResponse]
    payments: list[PaymentResponse]
    shipments: list[ShipmentResponse]


class ConversationSummaryResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationMessageResponse(
    BaseModel
):
    id: uuid.UUID
    role: str
    content: str
    route: str | None
    ui: SupportUIResponse | None = None
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageResponse]

class ChatRequest(BaseModel):
    request_id: uuid.UUID

    message: str = Field(
        min_length=1,
        max_length=4000,
    )

    conversation_id: uuid.UUID | None = None