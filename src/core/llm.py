from __future__ import annotations

from langchain_groq import ChatGroq

from src.core.config import (
    GROQ_API_KEY,
    LLM_TIMEOUT_SECONDS,
)


def create_chat_groq() -> ChatGroq:
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=GROQ_API_KEY,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=2,
    )