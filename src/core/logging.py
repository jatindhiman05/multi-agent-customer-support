from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from src.core.context import (
    get_conversation_id,
    get_request_id,
)


STANDARD_LOG_RECORD_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()

        if request_id is not None:
            payload["request_id"] = request_id

        conversation_id = (
            get_conversation_id()
        )

        if conversation_id is not None:
            payload[
                "conversation_id"
            ] = conversation_id

        # Include explicitly supplied structured fields.
        for key, value in record.__dict__.items():
            if (
                key
                not in STANDARD_LOG_RECORD_FIELDS
                and not key.startswith("_")
                and key
                not in {
                    "message",
                    "asctime",
                }
            ):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            payload,
            default=str,
        )


def configure_logging(
    level: int = logging.INFO,
) -> None:
    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setFormatter(
        JsonFormatter()
    )

    root_logger = logging.getLogger()

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    logging.getLogger(
        "httpx"
    ).setLevel(
        logging.WARNING
    )

def get_logger(
    name: str,
) -> logging.Logger:
    return logging.getLogger(name)