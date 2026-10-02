import uuid

from sqlalchemy.orm import Session

from src.db.models.conversation import Conversation


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
    ) -> Conversation:

        conversation = Conversation(
            customer_id=customer_id,
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