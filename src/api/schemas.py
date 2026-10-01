import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
    )

    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    route: str
    conversation_id: str


def create_conversation_id() -> str:
    return str(uuid.uuid4())