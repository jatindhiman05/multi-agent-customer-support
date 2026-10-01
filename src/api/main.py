from fastapi import Depends, FastAPI
from langchain_core.messages import HumanMessage

from src.api.dependencies import get_current_customer_id
from src.api.schemas import ChatRequest, ChatResponse
from src.graph.graph import support_graph


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
    result = support_graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=request.message
                )
            ],
            "route": None,
            "customer_id": customer_id,
        }
    )

    return ChatResponse(
        response=result["messages"][-1].content,
        route=result["route"],
    )