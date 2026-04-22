from app.core.settings import settings


def get_llm_adapter(provider: str | None = None):
    target = (provider or settings.LLM_PROVIDER).lower()

    if target == "openai":
        from app.services.llm_adapters.openai_adapter import OpenAiAdapter
        return OpenAiAdapter()

    if target == "ollama":
        from app.services.llm_adapters.ollama_adapter import OllamaAdapter
        return OllamaAdapter()

    raise ValueError(f"지원하지 않는 provider 입니다: {target}")