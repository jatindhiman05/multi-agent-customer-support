from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from langchain_core.messages import HumanMessage
from sqlalchemy.exc import IntegrityError

from src.api.schemas import ChatRequest
from src.core.context import (
    reset_conversation_id,
    reset_token_sink,
    set_conversation_id,
    set_token_sink,
)
from src.db.models import ChatRequestRecord
from src.db.session import SessionLocal
from src.graph.graph import support_graph
from src.repositories.chat_request_repository import (
    ChatRequestRepository,
)
from src.services.conversation_service import (
    ConversationService,
)


logger = logging.getLogger(__name__)


class ChatRequestConflictError(Exception):
    """Request ID was reused for different request content."""


class ChatRequestInProgressError(Exception):
    """The same logical request is already being processed."""


@dataclass(slots=True)
class ChatExecutionResult:
    response: str
    route: str
    conversation_id: uuid.UUID
    ui: dict[str, Any] | None = None
    replayed: bool = False


@dataclass(slots=True)
class ChatRequestClaim:
    conversation_id: uuid.UUID | None
    is_retry: bool = False


class ChatService:
    def execute(
        self,
        *,
        request: ChatRequest,
        customer_id: str,
        token_sink: Callable[[str], None] | None = None,
    ) -> ChatExecutionResult:
        start_time = time.perf_counter()

        customer_uuid = uuid.UUID(
            customer_id
        )

        request_hash = self._request_hash(
            message=request.message,
            conversation_id=request.conversation_id,
        )

        claim_result = self._claim_request(
            request=request,
            customer_uuid=customer_uuid,
            request_hash=request_hash,
        )

        if isinstance(
            claim_result,
            ChatExecutionResult,
        ):
            return claim_result

        logger.info(
            "chat.started",
            extra={
                "chat_request_id": str(
                    request.request_id
                ),
                "is_retry": (
                    claim_result.is_retry
                ),
            },
        )

        if claim_result.is_retry:
            if (
                claim_result.conversation_id
                is None
            ):
                raise RuntimeError(
                    "Failed chat request has no "
                    "conversation associated with it."
                )

            conversation_id = (
                claim_result.conversation_id
            )

        else:
            conversation_id = (
                self._persist_initial_user_message(
                    request=request,
                    customer_uuid=customer_uuid,
                )
            )

            self._attach_conversation(
                customer_uuid=customer_uuid,
                request_id=request.request_id,
                conversation_id=conversation_id,
            )

        conversation_token = (
            set_conversation_id(
                str(conversation_id)
            )
        )

        token_sink_token = None

        if token_sink is not None:
            token_sink_token = set_token_sink(
                token_sink
            )

        try:
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
                config={
                    "configurable": {
                        "thread_id": str(
                            conversation_id
                        ),
                    }
                },
            )

            route = result["route"]
            ui_payload = result.get("ui")

            response_content = (
                result["messages"][-1].content
            )

            self._persist_success(
                customer_uuid=customer_uuid,
                request_id=request.request_id,
                conversation_id=conversation_id,
                response_content=response_content,
                route=route,
                ui_payload=ui_payload,
            )

            duration_ms = (
                time.perf_counter()
                - start_time
            ) * 1000

            logger.info(
                "chat.completed",
                extra={
                    "chat_request_id": str(
                        request.request_id
                    ),
                    "route": route,
                    "duration_ms": round(
                        duration_ms,
                        2,
                    ),
                    "is_retry": (
                        claim_result.is_retry
                    ),
                },
            )

            return ChatExecutionResult(
                response=response_content,
                route=route,
                conversation_id=conversation_id,
                ui=ui_payload,
            )

        except Exception:
            logger.exception(
                "chat.failed",
                extra={
                    "chat_request_id": str(
                        request.request_id
                    ),
                },
            )

            self._mark_failed(
                customer_uuid=customer_uuid,
                request_id=request.request_id,
                conversation_id=conversation_id,
            )

            raise

        finally:
            if token_sink_token is not None:
                reset_token_sink(
                    token_sink_token
                )

            reset_conversation_id(
                conversation_token
            )

    def _claim_request(
        self,
        *,
        request: ChatRequest,
        customer_uuid: uuid.UUID,
        request_hash: str,
    ) -> (
        ChatExecutionResult
        | ChatRequestClaim
    ):
        with SessionLocal() as session:
            repository = (
                ChatRequestRepository(
                    session
                )
            )

            existing = repository.get(
                customer_id=customer_uuid,
                request_id=request.request_id,
            )

            if existing is not None:
                return (
                    self._handle_existing_request(
                        session=session,
                        existing=existing,
                        request_hash=request_hash,
                    )
                )

            record = ChatRequestRecord(
                customer_id=customer_uuid,
                request_id=request.request_id,
                request_hash=request_hash,
                status="processing",
            )

            repository.add(
                record
            )

            try:
                session.commit()

            except IntegrityError:
                session.rollback()

                existing = repository.get(
                    customer_id=customer_uuid,
                    request_id=request.request_id,
                )

                if existing is None:
                    raise

                return (
                    self._handle_existing_request(
                        session=session,
                        existing=existing,
                        request_hash=request_hash,
                    )
                )

        return ChatRequestClaim(
            conversation_id=None,
            is_retry=False,
        )

    def _handle_existing_request(
        self,
        *,
        session,
        existing: ChatRequestRecord,
        request_hash: str,
    ) -> (
        ChatExecutionResult
        | ChatRequestClaim
    ):
        if (
            existing.request_hash
            != request_hash
        ):
            raise ChatRequestConflictError(
                "This request ID has already "
                "been used for a different "
                "chat request."
            )

        if existing.status == "completed":
            if (
                existing.conversation_id
                is None
                or existing.response_content
                is None
                or existing.route is None
            ):
                raise RuntimeError(
                    "Completed chat request "
                    "has incomplete result."
                )

            logger.info(
                "chat.idempotent_replay",
                extra={
                    "chat_request_id": str(
                        existing.request_id
                    ),
                },
            )

            return ChatExecutionResult(
                response=(
                    existing.response_content
                ),
                route=existing.route,
                conversation_id=(
                    existing.conversation_id
                ),
                ui=existing.ui_payload,
                replayed=True,
            )

        if existing.status == "processing":
            raise ChatRequestInProgressError(
                "This chat request is already "
                "being processed."
            )

        if existing.status == "failed":
            if (
                existing.conversation_id
                is None
            ):
                raise RuntimeError(
                    "Failed chat request has no "
                    "conversation associated with it."
                )

            conversation_id = (
                existing.conversation_id
            )

            existing.status = "processing"

            session.commit()

            logger.info(
                "chat.retry_started",
                extra={
                    "chat_request_id": str(
                        existing.request_id
                    ),
                    "conversation_id": str(
                        conversation_id
                    ),
                },
            )

            return ChatRequestClaim(
                conversation_id=conversation_id,
                is_retry=True,
            )

        raise RuntimeError(
            "Chat request has an unknown status: "
            f"{existing.status!r}."
        )

    def _persist_initial_user_message(
        self,
        *,
        request: ChatRequest,
        customer_uuid: uuid.UUID,
    ) -> uuid.UUID:
        with SessionLocal() as session:
            service = ConversationService(
                session
            )

            if (
                request.conversation_id
                is None
            ):
                conversation = (
                    service.create(
                        customer_id=(
                            customer_uuid
                        ),
                        first_message=(
                            request.message
                        ),
                    )
                )

                logger.info(
                    "conversation.created",
                    extra={
                        "conversation_id_created": (
                            str(
                                conversation.id
                            )
                        ),
                    },
                )

            else:
                conversation = (
                    service.get_for_customer(
                        conversation_id=(
                            request.conversation_id
                        ),
                        customer_id=(
                            customer_uuid
                        ),
                    )
                )

            service.add_message(
                conversation=conversation,
                role="user",
                content=request.message,
            )

            session.commit()

            return conversation.id

    def _attach_conversation(
        self,
        *,
        customer_uuid: uuid.UUID,
        request_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> None:
        with SessionLocal() as session:
            repository = (
                ChatRequestRepository(
                    session
                )
            )

            record = repository.get(
                customer_id=customer_uuid,
                request_id=request_id,
            )

            if record is None:
                raise RuntimeError(
                    "Chat request idempotency "
                    "record disappeared."
                )

            if record.status != "processing":
                raise RuntimeError(
                    "Chat request is no longer "
                    "in processing state."
                )

            record.conversation_id = (
                conversation_id
            )

            session.commit()

    def _persist_success(
        self,
        *,
        customer_uuid: uuid.UUID,
        request_id: uuid.UUID,
        conversation_id: uuid.UUID,
        response_content: str,
        route: str,
        ui_payload: dict[str, Any] | None,
    ) -> None:
        with SessionLocal() as session:
            service = ConversationService(
                session
            )

            conversation = (
                service.get_for_customer(
                    conversation_id=(
                        conversation_id
                    ),
                    customer_id=(
                        customer_uuid
                    ),
                )
            )

            repository = (
                ChatRequestRepository(
                    session
                )
            )

            request_record = (
                repository.get(
                    customer_id=(
                        customer_uuid
                    ),
                    request_id=request_id,
                )
            )

            if request_record is None:
                raise RuntimeError(
                    "Chat request idempotency "
                    "record disappeared."
                )

            if (
                request_record.status
                != "processing"
            ):
                raise RuntimeError(
                    "Chat request is no longer "
                    "in processing state."
                )

            if (
                request_record.conversation_id
                != conversation_id
            ):
                raise RuntimeError(
                    "Chat request conversation "
                    "does not match execution "
                    "conversation."
                )

            service.add_message(
                conversation=conversation,
                role="assistant",
                content=response_content,
                route=route,
                ui_payload=ui_payload,
            )

            request_record.status = (
                "completed"
            )
            request_record.response_content = (
                response_content
            )
            request_record.route = route
            request_record.ui_payload = (
                ui_payload
            )

            session.commit()

    def _mark_failed(
        self,
        *,
        customer_uuid: uuid.UUID,
        request_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> None:
        with SessionLocal() as session:
            repository = (
                ChatRequestRepository(
                    session
                )
            )

            record = repository.get(
                customer_id=customer_uuid,
                request_id=request_id,
            )

            if record is None:
                logger.error(
                    "chat.failure_record_missing",
                    extra={
                        "chat_request_id": str(
                            request_id
                        ),
                    },
                )
                return

            if record.status == "completed":
                return

            record.status = "failed"

            if (
                record.conversation_id
                is None
            ):
                record.conversation_id = (
                    conversation_id
                )

            session.commit()

    @staticmethod
    def _request_hash(
        *,
        message: str,
        conversation_id: (
            uuid.UUID | None
        ),
    ) -> str:
        payload = {
            "message": message,
            "conversation_id": (
                str(conversation_id)
                if conversation_id
                is not None
                else None
            ),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()