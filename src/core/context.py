from __future__ import annotations

from contextvars import ContextVar, Token


_request_id: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

_conversation_id: ContextVar[str | None] = ContextVar(
    "conversation_id",
    default=None,
)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(
    request_id: str,
) -> Token:
    return _request_id.set(request_id)


def reset_request_id(
    token: Token,
) -> None:
    _request_id.reset(token)


def get_conversation_id() -> str | None:
    return _conversation_id.get()


def set_conversation_id(
    conversation_id: str,
) -> Token:
    return _conversation_id.set(
        conversation_id
    )


def reset_conversation_id(
    token: Token,
) -> None:
    _conversation_id.reset(token)