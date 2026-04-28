from typing import TypedDict, Any


class RagState(TypedDict, total=False):
    user_message: str
    original_query: str
    rewritten_query: str

    conversation_id: int | None
    is_new_conversation: bool

    llm_provider: str
    requested_provider: str
    used_provider: str | None

    system_prompt: str
    user_prompt: str

    sources: list[dict]
    eval_result: str

    answer: str
    retry_count: int

    metadata: dict[str, Any]