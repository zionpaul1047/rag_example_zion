import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.settings import settings


SESSION_ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".html", ".htm", ".pdf", ".docx",
    ".png", ".jpg", ".jpeg", ".xlsx", ".csv", ".pptx", ".hwpx"
}

MANAGED_ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".html", ".htm", ".pdf", ".docx",
    ".xlsx", ".csv", ".pptx", ".hwpx"
}


def ensure_directories():
    Path(settings.SESSION_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.MANAGED_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_extension(filename: str, scope: str):
    ext = get_extension(filename)

    if scope == "session":
        allowed = SESSION_ALLOWED_EXTENSIONS
    elif scope == "managed":
        allowed = MANAGED_ALLOWED_EXTENSIONS
    else:
        raise ValueError(f"지원하지 않는 scope 입니다: {scope}")

    if ext not in allowed:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")


def classify_file_type(filename: str) -> str:
    ext = get_extension(filename)

    if ext in {".txt", ".md", ".html", ".htm", ".pdf", ".docx"}:
        return "text_like"

    if ext in {".png", ".jpg", ".jpeg"}:
        return "image"

    if ext in {".xlsx", ".csv"}:
        return "structured"

    if ext in {".pptx"}:
        return "presentation"

    if ext in {".hwpx"}:
        return "limited"

    return "unknown"


def save_upload_file(upload_file: UploadFile, scope: str) -> dict:
    ensure_directories()
    validate_extension(upload_file.filename or "", scope)

    ext = get_extension(upload_file.filename or "")
    file_id = uuid4().hex

    base_dir = Path(settings.SESSION_UPLOAD_DIR) if scope == "session" else Path(settings.MANAGED_UPLOAD_DIR)
    saved_name = f"{file_id}{ext}"
    saved_path = base_dir / saved_name

    size_bytes = 0

    with saved_path.open("wb") as buffer:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break
            size_bytes += len(chunk)
            buffer.write(chunk)

            if size_bytes > settings.MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024:
                buffer.close()
                saved_path.unlink(missing_ok=True)
                raise ValueError(f"업로드 가능 최대 크기({settings.MAX_UPLOAD_FILE_SIZE_MB}MB)를 초과했습니다.")

    return {
        "original_name": upload_file.filename,
        "saved_name": saved_name,
        "saved_path": str(saved_path),
        "mime_type": upload_file.content_type or "application/octet-stream",
        "file_size": size_bytes,
        "file_extension": ext,
        "file_category": classify_file_type(upload_file.filename or "")
    }