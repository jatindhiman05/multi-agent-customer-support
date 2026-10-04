from __future__ import annotations

import json
import queue
import threading

import logging

import time

import uuid

from sqlalchemy import select, text

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

    reset_request_id,

    set_request_id,

)



from src.core.logging import (

    configure_logging,

    get_logger,

)

from src.db.session import SessionLocal
from fastapi.responses import StreamingResponse
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



from src.services.chat_service import (

    ChatRequestConflictError,

    ChatRequestInProgressError,

    ChatService,

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



    try:

        result = ChatService().execute(

            request=request,

            customer_id=customer_id,

        )



        return ChatResponse(

            response=result.response,

            route=result.route,

            conversation_id=(

                result.conversation_id

            ),

            ui=result.ui,

        )



    except ChatRequestConflictError as exc:

        raise HTTPException(

            status_code=409,

            detail=str(exc),

        ) from exc



    except ChatRequestInProgressError as exc:

        raise HTTPException(

            status_code=409,

            detail=str(exc),

        ) from exc




@app.post(
    "/chat/stream",
)
def chat_stream(
    request: ChatRequest,
    customer_id: str = Depends(
        get_current_customer_id
    ),
):
    chat_rate_limiter.check(
        key=customer_id,
    )

    def event_stream():
        events: queue.Queue[
            tuple[str, object]
        ] = queue.Queue()

        finished = object()

        def emit_event(
            event_type: str,
            payload: object,
        ) -> None:
            events.put(
                (
                    event_type,
                    payload,
                )
            )

        def emit_token(
            token: str,
        ) -> None:
            emit_event(
                "token",
                token,
            )

        def execute_chat() -> None:
            try:
                result = ChatService().execute(
                    request=request,
                    customer_id=customer_id,
                    token_sink=emit_token,
                )

                emit_event(
                    "final",
                    result,
                )

            except ChatRequestConflictError as exc:
                emit_event(
                    "error",
                    {
                        "code": (
                            "request_conflict"
                        ),
                        "message": str(exc),
                        "status_code": 409,
                    },
                )

            except ChatRequestInProgressError as exc:
                emit_event(
                    "error",
                    {
                        "code": (
                            "request_in_progress"
                        ),
                        "message": str(exc),
                        "status_code": 409,
                    },
                )

            except Exception:
                logger.exception(
                    "chat.stream_failed",
                    extra={
                        "chat_request_id": str(
                            request.request_id
                        ),
                    },
                )

                emit_event(
                    "error",
                    {
                        "code": (
                            "chat_execution_failed"
                        ),
                        "message": (
                            "The support request "
                            "could not be completed."
                        ),
                        "status_code": 500,
                    },
                )

            finally:
                events.put(
                    (
                        "finished",
                        finished,
                    )
                )

        yield (
            json.dumps(
                {
                    "type": "started",
                    "request_id": str(
                        request.request_id
                    ),
                },
                separators=(",", ":"),
            )
            + "\n"
        )

        worker = threading.Thread(
            target=execute_chat,
            name=(
                "chat-stream-"
                f"{request.request_id}"
            ),
            daemon=False,
        )

        worker.start()

        while True:
            event_type, payload = (
                events.get()
            )

            if (
                event_type == "finished"
                and payload is finished
            ):
                break

            if event_type == "token":
                yield (
                    json.dumps(
                        {
                            "type": "token",
                            "delta": payload,
                        },
                        separators=(",", ":"),
                    )
                    + "\n"
                )

                continue

            if event_type == "final":
                result = payload

                yield (
                    json.dumps(
                        {
                            "type": "final",
                            "response": (
                                result.response
                            ),
                            "route": (
                                result.route
                            ),
                            "conversation_id": str(
                                result.conversation_id
                            ),
                            "ui": result.ui,
                            "replayed": (
                                result.replayed
                            ),
                        },
                        separators=(",", ":"),
                    )
                    + "\n"
                )

                continue

            if event_type == "error":
                yield (
                    json.dumps(
                        {
                            "type": "error",
                            **payload,
                        },
                        separators=(",", ":"),
                    )
                    + "\n"
                )

        worker.join()

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": (
                "no-cache, no-transform"
            ),
            "X-Accel-Buffering": "no",
        },
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



@app.delete(

    "/conversations/{conversation_id}",

    status_code=204,

)

def delete_conversation(

    conversation_id: uuid.UUID,

    customer_id: str = Depends(

        get_current_customer_id

    ),

):

    customer_uuid = uuid.UUID(customer_id)



    with SessionLocal() as session:

        service = ConversationService(session)



        service.delete_for_customer(

            conversation_id=conversation_id,

            customer_id=customer_uuid,

        )



        session.commit()