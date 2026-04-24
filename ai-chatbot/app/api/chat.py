import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.rag_service import ask_rag, ask_rag_stream

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None
    stream: bool = False
    llm_provider: str | None = None


@router.post("/chat")
def chat(request: ChatRequest):
    provider = request.llm_provider or "auto"

    if request.stream:
        def event_generator():
            for item in ask_rag_stream(
                request.message,
                conversation_id=request.conversation_id,
                llm_provider=provider,
            ):
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )

    return ask_rag(
        request.message,
        conversation_id=request.conversation_id,
        llm_provider=provider,
    )