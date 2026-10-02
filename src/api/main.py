import uuid

from fastapi import Depends, FastAPI, HTTPException
from langchain_core.messages import HumanMessage

from src.api.dependencies import get_current_customer_id
from src.api.schemas import ChatRequest, ChatResponse
from src.db.session import SessionLocal
from src.graph.graph import support_graph
from src.services.conversation_service import (
    ConversationAccessDeniedError,
    ConversationNotFoundError,
    ConversationService,
)

app = FastAPI(
    title="VoltNest Customer Support",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    customer_uuid = uuid.UUID(customer_id)

    with SessionLocal() as session:

        service = ConversationService(session)

        if request.conversation_id is None:

            conversation = service.create(
                customer_id=customer_uuid,
            )

            session.commit()

        else:
            try:
                conversation = service.get_for_customer(
                    conversation_id=request.conversation_id,
                    customer_id=customer_uuid,
                )

            except ConversationNotFoundError:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found.",
                )

            except ConversationAccessDeniedError:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to this conversation.",
                )

    conversation_id = conversation.id

    config = {
        "configurable": {
            "thread_id": str(conversation_id),
        }
    }

    result = support_graph.invoke(
        {
            "messages": [
                HumanMessage(content=request.message)
            ],
            "customer_id": str(customer_id),
        },
        config=config,
    )

    return ChatResponse(
        response=result["messages"][-1].content,
        route=result["route"],
        conversation_id=conversation_id,
    )