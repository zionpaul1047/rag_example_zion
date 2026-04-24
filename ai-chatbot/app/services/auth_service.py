from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 개발용 임시 사용자
# 실무에서는 DB users 테이블로 이동해야 함
DEV_USERS = {
    "zion": {
        "username": "zion",
        "display_name": "이지온",
        "role": "user",
        # password: user1234
        "password_hash": pwd_context.hash("user1234"),
    },
    "admin": {
        "username": "admin",
        "display_name": "관리자",
        "role": "admin",
        # password: admin1234
        "password_hash": pwd_context.hash("admin1234"),
    },
}


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def authenticate_user(username: str, password: str) -> dict | None:
    user = DEV_USERS.get(username)
    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
    }


def create_access_token(user: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    payload = {
        "sub": user["username"],
        "role": user["role"],
        "display_name": user["display_name"],
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise ValueError("유효하지 않은 토큰입니다.") from e


def get_user_from_token(token: str) -> dict:
    payload = decode_access_token(token)

    username = payload.get("sub")
    role = payload.get("role")
    display_name = payload.get("display_name")

    if not username or not role:
        raise ValueError("토큰 정보가 올바르지 않습니다.")

    return {
        "username": username,
        "role": role,
        "display_name": display_name or username,
    }