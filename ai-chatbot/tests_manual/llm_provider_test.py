from app.core.settings import settings
from app.services.llm_adapters.factory import get_llm_adapter

print("LLM_PROVIDER =", settings.LLM_PROVIDER)
print("OLLAMA_MODEL =", settings.OLLAMA_MODEL)
print("OLLAMA_BASE_URL =", settings.OLLAMA_BASE_URL)
print("OPENAI_CHAT_MODEL =", settings.OPENAI_CHAT_MODEL)
print()

adapter = get_llm_adapter()
answer = adapter.generate(
    system_prompt="당신은 테스트용 AI입니다.",
    user_prompt="간단하게 한 줄 자기소개 해줘."
)

print("[응답]")
print(answer)