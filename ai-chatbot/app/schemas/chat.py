from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class SourceItem(BaseModel):
    source: str
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]