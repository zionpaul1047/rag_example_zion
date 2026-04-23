from pydantic import BaseModel


class SessionUploadResponse(BaseModel):
    id: int
    scope: str
    original_name: str
    file_category: str
    doc_status: str
    conversation_id: int | None = None


class ManagedUploadResponse(BaseModel):
    id: int
    scope: str
    title: str
    category: str | None = None
    original_name: str
    file_category: str
    status: str