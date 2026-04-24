from app.services.llm_adapters.factory import get_llm_adapter
from app.services.llm_routing_service import generate_with_routing


def generate_title(user_message: str, provider: str = "auto") -> str:
    system_prompt = """
당신은 대화 제목 생성기입니다.

규칙:
- 한국어로 작성
- 20자 이내
- 핵심 주제만 표현
- 따옴표 금지
- 번호 금지
- 설명 금지
"""

    user_prompt = f"질문: {user_message}"

    try:
        provider = (provider or "auto").lower()

        if provider == "auto":
            result, _ = generate_with_routing(system_prompt, user_prompt)
        else:
            adapter = get_llm_adapter(provider)
            result = adapter.generate(system_prompt, user_prompt)

        title = (result or "").strip()
        title = title.replace('"', "").replace("'", "")
        title = " ".join(title.split())

        if len(title) > 20:
            title = title[:20]

        return title or fallback_title(user_message)

    except Exception:
        return fallback_title(user_message)


def fallback_title(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    return cleaned[:20] if cleaned else "새 대화"