from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar, Token


TokenSink = Callable[[str], None]


_request_id: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

_conversation_id: ContextVar[str | None] = ContextVar(
    "conversation_id",
    default=None,
)

_token_sink: ContextVar[TokenSink | None] = ContextVar(
    "token_sink",
    default=None,
)


# ---------------------------------------------------------------------
# Request ID
# ---------------------------------------------------------------------


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


# ---------------------------------------------------------------------
# Conversation ID
# ---------------------------------------------------------------------


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


# ---------------------------------------------------------------------
# Customer-facing token streaming
# ---------------------------------------------------------------------


def get_token_sink() -> TokenSink | None:
    """
    Return the token sink for the current request.

    None means the current request is using the normal
    non-streaming execution path.
    """
    return _token_sink.get()


def set_token_sink(
    sink: TokenSink,
) -> Token:
    """
    Install a request-scoped sink for safe customer-facing
    LLM tokens.

    Only explicitly approved final-generation boundaries
    should write to this sink.
    """
    return _token_sink.set(sink)


def reset_token_sink(
    token: Token,
) -> None:
    _token_sink.reset(token)


def emit_token(
    token: str,
) -> None:
    """
    Emit a customer-facing token when streaming is active.

    When no sink is installed this intentionally becomes
    a no-op.
    """
    if not token:
        return

    sink = get_token_sink()

    if sink is not None:
        sink(token)