import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
    )

    conversation_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    response: str
    route: str
    conversation_id: uuid.UUID

class LoginRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=255,
    )

    password: str = Field(
        min_length=8,
        max_length=256,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"