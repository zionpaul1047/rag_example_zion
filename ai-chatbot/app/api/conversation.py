from fastapi import APIRouter, Header, HTTPException

from app.services.auth_service import get_user_from_token
from app.services.conversation_service import (
    list_conversations,
    get_conversation_messages,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _get_current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다.")

    token = authorization.replace("Bearer ", "", 1)

    try:
        return get_user_from_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.get("")
def get_conversations(authorization: str | None = Header(default=None)):
    user = _get_current_user(authorization)
    return list_conversations(user["username"])


@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    authorization: str | None = Header(default=None),
):
    _get_current_user(authorization)
    return get_conversation_messages(conversation_id)