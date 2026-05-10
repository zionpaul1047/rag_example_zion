from fastapi import Header, HTTPException

from app.services.auth_service import get_user_from_token


def require_authenticated_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")

    token = authorization.replace("Bearer ", "", 1)

    try:
        return get_user_from_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


def require_admin_user(authorization: str | None = Header(default=None)) -> dict:
    user = require_authenticated_user(authorization)

    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

    return user
