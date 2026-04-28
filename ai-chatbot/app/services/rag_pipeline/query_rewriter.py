from app.services.chat_history_service import get_recent_messages
from app.services.llm_adapters.factory import get_llm_adapter
from app.services.llm_routing_service import generate_with_routing


def should_rewrite_query(user_message: str, conversation_id: int | None) -> bool:
    if conversation_id is None:
        return False

    text = " ".join(user_message.strip().split())

    if len(text) <= 12:
        return True

    ambiguous_words = [
        "그럼",
        "그거",
        "이거",
        "저거",
        "다음",
        "어떻게",
        "왜",
        "계속",
        "안돼",
        "안되",
        "해봤어",
    ]

    return any(word in text for word in ambiguous_words)


def rewrite_query(user_message: str, conversation_id: int | None, provider: str = "auto") -> str:
    if not should_rewrite_query(user_message, conversation_id):
        return user_message

    history = get_recent_messages(conversation_id, limit=6)

    if not history:
        return user_message

    history_text = "\n".join(
        f"{item['role']}: {item['content']}" for item in history
    )

    system_prompt = """
당신은 RAG 검색용 질문 재작성기입니다.

규칙:
- 사용자의 현재 질문을 이전 대화 맥락과 합쳐서 검색에 적합한 질문으로 바꾸세요.
- 한국어로 작성하세요.
- 1문장만 작성하세요.
- 설명하지 마세요.
- 따옴표를 쓰지 마세요.
- 원래 의미를 바꾸지 마세요.
"""

    user_prompt = f"""
[이전 대화]
{history_text}

[현재 질문]
{user_message}

[검색용 질문]
"""

    try:
        provider = (provider or "auto").lower()

        if provider == "auto":
            result, _ = generate_with_routing(system_prompt, user_prompt)
        else:
            adapter = get_llm_adapter(provider)
            result = adapter.generate(system_prompt, user_prompt)

        rewritten = " ".join((result or "").strip().split())

        if not rewritten:
            return user_message

        if len(rewritten) > 120:
            rewritten = rewritten[:120]

        return rewritten

    except Exception:
        return user_message