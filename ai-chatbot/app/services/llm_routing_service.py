from app.core.settings import settings
from app.services.llm_adapters.factory import get_llm_adapter


def _should_use_fallback_first(user_prompt: str) -> bool:
    if len(user_prompt) > settings.LLM_AUTO_SWITCH_MAX_CHARS:
        return True
    return False


def generate_with_routing(system_prompt: str, user_prompt: str) -> tuple[str, str]:
    mode = settings.LLM_PROVIDER.lower()

    if mode in ("openai", "ollama"):
        adapter = get_llm_adapter(mode)
        answer = adapter.generate(system_prompt, user_prompt)
        return answer, mode

    if mode != "auto":
        raise ValueError(f"지원하지 않는 LLM_PROVIDER 입니다: {settings.LLM_PROVIDER}")

    primary = settings.PRIMARY_LLM_PROVIDER.lower()
    fallback = settings.FALLBACK_LLM_PROVIDER.lower()

    first_provider = fallback if _should_use_fallback_first(user_prompt) else primary
    second_provider = primary if first_provider == fallback else fallback

    try:
        adapter = get_llm_adapter(first_provider)
        answer = adapter.generate(system_prompt, user_prompt)
        return answer, first_provider
    except Exception as first_error:
        print(f"[라우팅] 1차 provider 실패: {first_provider} / {first_error}")

    adapter = get_llm_adapter(second_provider)
    answer = adapter.generate(system_prompt, user_prompt)
    return answer, second_provider


def stream_with_routing(system_prompt: str, user_prompt: str):
    mode = settings.LLM_PROVIDER.lower()

    if mode in ("openai", "ollama"):
        adapter = get_llm_adapter(mode)
        for token in adapter.stream(system_prompt, user_prompt):
            yield token, mode
        return

    if mode != "auto":
        raise ValueError(f"지원하지 않는 LLM_PROVIDER 입니다: {settings.LLM_PROVIDER}")

    primary = settings.PRIMARY_LLM_PROVIDER.lower()
    fallback = settings.FALLBACK_LLM_PROVIDER.lower()

    first_provider = fallback if _should_use_fallback_first(user_prompt) else primary
    second_provider = primary if first_provider == fallback else fallback

    try:
        adapter = get_llm_adapter(first_provider)
        for token in adapter.stream(system_prompt, user_prompt):
            yield token, first_provider
        return
    except Exception as first_error:
        print(f"[라우팅] 스트리밍 1차 provider 실패: {first_provider} / {first_error}")

    adapter = get_llm_adapter(second_provider)
    for token in adapter.stream(system_prompt, user_prompt):
        yield token, second_provider