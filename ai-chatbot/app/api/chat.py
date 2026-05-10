import json
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.rag_service import ask_rag, ask_rag_stream
from app.services.auth_service import get_user_from_token
from app.services.conversation_service import conversation_belongs_to_user

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None
    stream: bool = False
    llm_provider: str | None = None


def _get_optional_username(authorization: str | None) -> str | None:
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰 형식이 올바르지 않습니다.")

    token = authorization.replace("Bearer ", "", 1)

    try:
        user = get_user_from_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    return user["username"]


def _validate_conversation_access(
    conversation_id: int | None,
    username: str | None,
):
    if conversation_id is None:
        return

    if username is None:
        raise HTTPException(status_code=401, detail="기존 대화를 이어가려면 로그인이 필요합니다.")

    if not conversation_belongs_to_user(conversation_id, username):
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")


@router.post("/chat")
def chat(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
):
    provider = request.llm_provider or "auto"
    username = _get_optional_username(authorization)
    _validate_conversation_access(request.conversation_id, username)

    if request.stream:
        def event_generator():
            for item in ask_rag_stream(
                request.message,
                conversation_id=request.conversation_id,
                llm_provider=provider,
                username=username,
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
        username=username,
    )
