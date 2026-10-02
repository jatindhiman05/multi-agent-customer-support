from __future__ import annotations

import logging
import time
import uuid
from sqlalchemy import select

from src.core.security import (
    create_access_token,
    verify_password,
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

from src.api.dependencies import (
    get_current_customer_id,
)
from src.api.schemas import (
    ChatRequest,
    ChatResponse,    
    LoginRequest,
    TokenResponse,
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


# ============================================================
# LOGGING
# ============================================================

configure_logging(
    level=logging.INFO,
)

logger = get_logger(__name__)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="VoltNest Customer Support",
    version="0.1.0",
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


@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
):
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
    start_time = time.perf_counter()

    customer_uuid = uuid.UUID(
        customer_id
    )

    logger.info(
        "chat.started"
    )

    with SessionLocal() as session:
        service = ConversationService(
            session
        )

        if request.conversation_id is None:
            conversation = service.create(
                customer_id=customer_uuid,
            )

            session.commit()

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
            response=(
                result["messages"][-1].content
            ),
            route=route,
            conversation_id=(
                conversation_id
            ),
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