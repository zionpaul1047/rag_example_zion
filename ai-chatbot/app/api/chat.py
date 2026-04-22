import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import ask_rag, ask_rag_stream

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if request.stream:
        def event_generator():
            for item in ask_rag_stream(
                user_message=request.message,
                conversation_id=request.conversation_id
            ):
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )

    result = ask_rag(
        user_message=request.message,
        conversation_id=request.conversation_id
    )

    return ChatResponse(**result)