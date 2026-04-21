from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ask_llm

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = ask_llm(request.message)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"]
    )