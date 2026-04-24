from fastapi import APIRouter, HTTPException, Header

from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_user_from_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    token = create_access_token(user)

    return LoginResponse(
        access_token=token,
        user=UserInfo(**user),
    )


@router.get("/me", response_model=UserInfo)
def me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다.")

    token = authorization.replace("Bearer ", "", 1)

    try:
        user = get_user_from_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    return UserInfo(**user)