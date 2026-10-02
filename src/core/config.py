from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

def _get_int_env(
    name: str,
    default: int,
    minimum: int = 1,
) -> int:
    raw_value = os.getenv(
        name,
        str(default),
    )

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be an integer."
        ) from exc

    if value < minimum:
        raise RuntimeError(
            f"{name} must be >= {minimum}."
        )

    return value


def _get_list_env(
    name: str,
    default: str = "",
) -> list[str]:
    raw_value = os.getenv(
        name,
        default,
    )

    return [
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    ]


ALLOWED_ORIGINS = _get_list_env(
    "ALLOWED_ORIGINS",
    "http://localhost:3000",
)

CHAT_RATE_LIMIT_PER_MINUTE = _get_int_env(
    "CHAT_RATE_LIMIT_PER_MINUTE",
    20,
)

LOGIN_RATE_LIMIT_PER_MINUTE = _get_int_env(
    "LOGIN_RATE_LIMIT_PER_MINUTE",
    10,
)

LLM_TIMEOUT_SECONDS = _get_int_env(
    "LLM_TIMEOUT_SECONDS",
    30,
)

def _required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"{name} is not configured. "
            "Create a .env file based on .env.example."
        )

    return value


DATABASE_URL = _required_env(
    "DATABASE_URL"
)

GROQ_API_KEY = _required_env(
    "GROQ_API_KEY"
)


JWT_SECRET = _required_env(
    "JWT_SECRET"
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = _get_int_env(
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    60,
)