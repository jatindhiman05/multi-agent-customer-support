from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from src.core.logging import get_logger


logger = get_logger("voltnest.observability")


@contextmanager
def observe_operation(
    operation: str,
    **fields,
) -> Iterator[None]:
    """
    Log the start, completion, duration, and failure of an operation.

    Never pass customer messages, prompts, secrets, credentials,
    or sensitive tool arguments through fields.
    """

    start_time = time.perf_counter()

    logger.info(
        f"{operation}.started",
        extra=fields,
    )

    try:
        yield

    except Exception:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.exception(
            f"{operation}.failed",
            extra={
                **fields,
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
            },
        )

        raise

    else:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.info(
            f"{operation}.completed",
            extra={
                **fields,
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
            },
        )