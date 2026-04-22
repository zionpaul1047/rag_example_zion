from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    sources: list[dict]