from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(
        self,
        requests: int,
        window_seconds: int = 60,
    ):
        self.requests = requests
        self.window_seconds = window_seconds

        self._requests: dict[
            str,
            deque[float],
        ] = defaultdict(deque)

        self._lock = threading.Lock()

    def check(
        self,
        key: str,
    ) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._requests[key]

            while (
                timestamps
                and timestamps[0] <= cutoff
            ):
                timestamps.popleft()

            if len(timestamps) >= self.requests:
                raise HTTPException(
                    status_code=(
                        status.HTTP_429_TOO_MANY_REQUESTS
                    ),
                    detail="Too many requests. Please try again later.",
                )

            timestamps.append(now)


def get_client_ip(
    request: Request,
) -> str:
    if request.client is None:
        return "unknown"

    return request.client.host