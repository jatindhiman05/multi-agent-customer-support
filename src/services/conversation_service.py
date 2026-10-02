import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.db.models.conversation import Conversation
from src.db.models.conversation_message import ConversationMessage


class ConversationNotFoundError(Exception):
    pass


class ConversationAccessDeniedError(Exception):
    pass


class ConversationService:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        customer_id: uuid.UUID,
        first_message: str | None = None,
    ) -> Conversation:
        conversation = Conversation(
            customer_id=customer_id,
            title=(
                self._make_title(first_message)
                if first_message
                else None
            ),
        )

        self.session.add(conversation)
        self.session.flush()

        return conversation

    def get_for_customer(
        self,
        conversation_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Conversation:
        conversation = self.session.get(
            Conversation,
            conversation_id,
        )

        if conversation is None:
            raise ConversationNotFoundError()

        if conversation.customer_id != customer_id:
            raise ConversationAccessDeniedError()

        return conversation

    def list_for_customer(
        self,
        customer_id: uuid.UUID,
    ) -> list[Conversation]:

        statement = (
            select(Conversation)
            .where(
                Conversation.customer_id == customer_id,
                Conversation.messages.any(),
            )
            .order_by(
                Conversation.updated_at.desc()
            )
        )
        return list(
            self.session.scalars(statement).all()
        )

    def get_with_messages(
        self,
        conversation_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Conversation:
        statement = (
            select(Conversation)
            .options(
                selectinload(
                    Conversation.messages
                )
            )
            .where(
                Conversation.id == conversation_id
            )
        )

        conversation = self.session.scalar(
            statement
        )

        if conversation is None:
            raise ConversationNotFoundError()

        if conversation.customer_id != customer_id:
            raise ConversationAccessDeniedError()

        return conversation

    def add_message(
        self,
        *,
        conversation: Conversation,
        role: str,
        content: str,
        route: str | None = None,
    ) -> ConversationMessage:
        if role not in {"user", "assistant"}:
            raise ValueError(
                "Conversation message role must be "
                "'user' or 'assistant'."
            )

        message = ConversationMessage(
            conversation_id=conversation.id,
            role=role,
            content=content,
            route=route,
        )

        conversation.updated_at = (
            datetime.now(timezone.utc)
        )

        self.session.add(message)
        self.session.flush()

        return message

    @staticmethod
    def _make_title(message: str) -> str:
        cleaned = " ".join(
            message.strip().split()
        )

        if len(cleaned) <= 80:
            return cleaned

        return f"{cleaned[:77].rstrip()}..."