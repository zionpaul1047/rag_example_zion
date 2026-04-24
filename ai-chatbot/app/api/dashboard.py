from fastapi import APIRouter, Header, HTTPException

from app.services.auth_service import get_user_from_token
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/admin/dashboard", tags=["dashboard"])


def _require_admin(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다.")

    token = authorization.replace("Bearer ", "", 1)

    try:
        user = get_user_from_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

    return user


@router.get("/summary")
def dashboard_summary(authorization: str | None = Header(default=None)):
    _require_admin(authorization)
    return get_dashboard_summary()