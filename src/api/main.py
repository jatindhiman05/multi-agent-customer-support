from __future__ import annotations

import logging
import time
import uuid
from sqlalchemy import select,text

from src.core.security import (
    create_access_token,
    verify_password,
)
from src.core.config import (
    CHAT_RATE_LIMIT_PER_MINUTE,
    LOGIN_RATE_LIMIT_PER_MINUTE,
)
from src.core.rate_limit import (
    InMemoryRateLimiter,
    get_client_ip,
)
from src.db.models import User
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import ALLOWED_ORIGINS
from src.api.dependencies import (
    get_current_customer_id,
)
from src.api.schemas import (
    ChatRequest,
    ChatResponse,
    CurrentUserResponse,
    LoginRequest,
    TokenResponse,
    ConversationHistoryResponse,
    ConversationMessageResponse,
    ConversationSummaryResponse,
)
from src.core.context import (
    get_request_id,
    reset_conversation_id,
    reset_request_id,
    set_conversation_id,
    set_request_id,
)
from src.core.logging import (
    configure_logging,
    get_logger,
)
from src.db.session import SessionLocal
from src.graph.graph import support_graph
from src.services.conversation_service import (
    ConversationAccessDeniedError,
    ConversationNotFoundError,
    ConversationService,
)
from src.api.schemas import (
    OrderDetailResponse,
    OrderItemResponse,
    OrderSummaryResponse,
    PaymentResponse,
    ShipmentResponse,
)

from src.services.order_service import (
    OrderNotFoundError,
    OrderService,
)
# ============================================================
# LOGGING
# ============================================================

configure_logging(
    level=logging.INFO,
)

logger = get_logger(__name__)

login_rate_limiter = InMemoryRateLimiter(
    requests=LOGIN_RATE_LIMIT_PER_MINUTE,
)

chat_rate_limiter = InMemoryRateLimiter(
    requests=CHAT_RATE_LIMIT_PER_MINUTE,
)
# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="VoltNest Customer Support",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
    ],
)
# ============================================================
# REQUEST CONTEXT / LOGGING MIDDLEWARE
# ============================================================

@app.middleware("http")
async def request_context_middleware(
    request: Request,
    call_next,
):
    request_id = (
        request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )

    request_id_token = set_request_id(
        request_id
    )

    start_time = time.perf_counter()

    logger.info(
        "request.started",
        extra={
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(
            request
        )

        duration_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        logger.info(
            "request.completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": (
                    response.status_code
                ),
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
            },
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        return response

    except Exception:
        duration_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        logger.exception(
            "request.failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
            },
        )

        raise

    finally:
        reset_request_id(
            request_id_token
        )


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(
    ConversationNotFoundError
)
async def conversation_not_found_handler(
    request: Request,
    exc: ConversationNotFoundError,
):
    logger.warning(
        "conversation.not_found"
    )

    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": (
                    "conversation_not_found"
                ),
                "message": (
                    "Conversation not found."
                ),
                "request_id": (
                    get_request_id()
                ),
            }
        },
    )


@app.exception_handler(
    ConversationAccessDeniedError
)
async def conversation_access_denied_handler(
    request: Request,
    exc: ConversationAccessDeniedError,
):
    logger.warning(
        "conversation.access_denied"
    )

    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": (
                    "conversation_access_denied"
                ),
                "message": (
                    "You do not have access "
                    "to this conversation."
                ),
                "request_id": (
                    get_request_id()
                ),
            }
        },
    )


@app.exception_handler(
    RequestValidationError
)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    logger.warning(
        "request.validation_failed",
        extra={
            "validation_errors": (
                exc.errors()
            ),
        },
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": (
                    "validation_error"
                ),
                "message": (
                    "The request data is invalid."
                ),
                "request_id": (
                    get_request_id()
                ),
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "application.unhandled_exception",
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__,
        ),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": (
                    "internal_server_error"
                ),
                "message": (
                    "An unexpected error occurred."
                ),
                "request_id": (
                    get_request_id()
                ),
            }
        },
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
    }

@app.get("/ready")
def readiness():
    try:
        with SessionLocal() as session:
            session.execute(
                text("SELECT 1")
            )

        return {
            "status": "ready",
            "checks": {
                "database": "ok",
            },
        }

    except Exception:
        logger.exception(
            "readiness.database_failed"
        )

        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {
                    "database": "unavailable",
                },
            },
        )

@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    http_request: Request,
):
    login_rate_limiter.check(
        key=get_client_ip(http_request),
    )
    with SessionLocal() as session:
        user = session.scalar(
            select(User).where(
                User.email == request.email
            )
        )

        # Keep invalid email and invalid password
        # indistinguishable to callers.
        if (
            user is None
            or not verify_password(
                request.password,
                user.password_hash,
            )
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            )

        if user.status != "active":
            raise HTTPException(
                status_code=403,
                detail="User account is not active.",
            )

        if user.role != "customer":
            raise HTTPException(
                status_code=403,
                detail="Customer access required.",
            )

        access_token = create_access_token(
            user.id
        )

        logger.info(
            "authentication.login_succeeded",
            extra={
                "user_id": str(user.id),
            },
        )

        return TokenResponse(
            access_token=access_token,
        )

@app.get(
    "/auth/me",
    response_model=CurrentUserResponse,
)
def get_current_user(
    customer_id: str = Depends(
        get_current_customer_id
    ),
) -> CurrentUserResponse:
    with SessionLocal() as session:
        user = session.get(
            User,
            uuid.UUID(customer_id),
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid access token.",
            )

        return CurrentUserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
        )

@app.get(
    "/orders",
    response_model=list[OrderSummaryResponse],
)
def list_orders(
    customer_id: str = Depends(get_current_customer_id),
):
    with SessionLocal() as session:
        service = OrderService(session)

        orders = service.list_customer_orders(
            customer_id=uuid.UUID(customer_id),
        )

        return [
            OrderSummaryResponse(
                order_number=order.order_number,
                status=order.status,
                total_amount=order.total_amount,
                currency=order.currency,
                created_at=order.created_at,
            )
            for order in orders
        ]


@app.get(
    "/orders/{order_number}",
    response_model=OrderDetailResponse,
)
def get_order_details(
    order_number: str,
    customer_id: str = Depends(get_current_customer_id),
):
    with SessionLocal() as session:
        service = OrderService(session)

        try:
            order = service.get_order(
                order_number=order_number,
                customer_id=uuid.UUID(customer_id),
            )
        except OrderNotFoundError:
            raise HTTPException(
                status_code=404,
                detail="Order not found.",
            )

        return OrderDetailResponse(
            order_number=order.order_number,
            status=order.status,
            subtotal=order.subtotal,
            shipping_amount=order.shipping_amount,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            currency=order.currency,
            shipping_recipient_name=order.shipping_recipient_name,
            shipping_line1=order.shipping_line1,
            shipping_line2=order.shipping_line2,
            shipping_city=order.shipping_city,
            shipping_state=order.shipping_state,
            shipping_postal_code=order.shipping_postal_code,
            shipping_country_code=order.shipping_country_code,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=[
                OrderItemResponse(
                    sku=item.sku,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                )
                for item in order.items
            ],
            payments=[
                PaymentResponse(
                    provider=payment.provider,
                    payment_method=payment.payment_method,
                    status=payment.status,
                    amount=payment.amount,
                    currency=payment.currency,
                )
                for payment in order.payments
            ],
            shipments=[
                ShipmentResponse(
                    carrier=shipment.carrier,
                    tracking_number=shipment.tracking_number,
                    status=shipment.status,
                    shipped_at=shipment.shipped_at,
                    estimated_delivery_at=shipment.estimated_delivery_at,
                    delivered_at=shipment.delivered_at,
                )
                for shipment in order.shipments
            ],
        )

# ============================================================
# CHAT
# ============================================================

@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    customer_id: str = Depends(
        get_current_customer_id
    ),
):
    chat_rate_limiter.check(
        key=customer_id,
    )

    start_time = time.perf_counter()

    customer_uuid = uuid.UUID(
        customer_id
    )

    logger.info(
        "chat.started"
    )

    # --------------------------------------------------------
    # Persist the customer's message first.
    # --------------------------------------------------------

    with SessionLocal() as session:
        service = ConversationService(
            session
        )

        if request.conversation_id is None:
            conversation = service.create(
                customer_id=customer_uuid,
                first_message=request.message,
            )

            logger.info(
                "conversation.created",
                extra={
                    "conversation_id_created": (
                        str(conversation.id)
                    ),
                },
            )

        else:
            conversation = (
                service.get_for_customer(
                    conversation_id=(
                        request.conversation_id
                    ),
                    customer_id=customer_uuid,
                )
            )

        service.add_message(
            conversation=conversation,
            role="user",
            content=request.message,
        )

        session.commit()

        conversation_id = conversation.id

    conversation_token = (
        set_conversation_id(
            str(conversation_id)
        )
    )

    try:
        config = {
            "configurable": {
                "thread_id": str(
                    conversation_id
                ),
            }
        }

        result = support_graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=request.message
                    )
                ],
                "customer_id": (
                    customer_id
                ),
            },
            config=config,
        )

        route = result["route"]
        ui_payload = result.get("ui")

        response_content = (
            result["messages"][-1].content
        )

        # ----------------------------------------------------
        # Persist successful assistant response.
        # ----------------------------------------------------

        with SessionLocal() as session:
            service = ConversationService(
                session
            )

            conversation = (
                service.get_for_customer(
                    conversation_id=(
                        conversation_id
                    ),
                    customer_id=customer_uuid,
                )
            )

            service.add_message(
                conversation=conversation,
                role="assistant",
                content=response_content,
                route=route,
                ui_payload=ui_payload,
            )

            session.commit()

        duration_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        logger.info(
            "chat.completed",
            extra={
                "route": route,
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
            },
        )

        return ChatResponse(
            response=response_content,
            route=route,
            conversation_id=conversation_id,
            ui=ui_payload,
        )

    except Exception:
        logger.exception(
            "chat.failed"
        )
        raise

    finally:
        reset_conversation_id(
            conversation_token
        )

# ============================================================
# CONVERSATIONS
# ============================================================


@app.get(
    "/conversations",
    response_model=list[ConversationSummaryResponse],
)
def list_conversations(
    customer_id: str = Depends(
        get_current_customer_id
    ),
):
    customer_uuid = uuid.UUID(customer_id)

    with SessionLocal() as session:
        service = ConversationService(session)

        conversations = service.list_for_customer(
            customer_id=customer_uuid,
        )

        return [
            ConversationSummaryResponse(
                id=conversation.id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
            for conversation in conversations
        ]


@app.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationHistoryResponse,
)
def get_conversation_messages(
    conversation_id: uuid.UUID,
    customer_id: str = Depends(
        get_current_customer_id
    ),
):
    customer_uuid = uuid.UUID(customer_id)

    with SessionLocal() as session:
        service = ConversationService(session)

        conversation = service.get_with_messages(
            conversation_id=conversation_id,
            customer_id=customer_uuid,
        )

        return ConversationHistoryResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[
                ConversationMessageResponse(
                    id=message.id,
                    role=message.role,
                    content=message.content,
                    route=message.route,
                    ui=message.ui_payload,
                    created_at=message.created_at,
                )
                for message in conversation.messages
            ],
        )