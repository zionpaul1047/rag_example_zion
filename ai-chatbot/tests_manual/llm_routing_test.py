from app.core.settings import settings
from app.services.llm_routing_service import generate_with_routing

system_prompt = "당신은 친절한 테스트용 AI입니다. 반드시 한국어로만 답하세요."
user_prompt = "TV 화면이 안 나와요. 어떻게 점검하면 좋을까요?"

print("LLM_PROVIDER =", settings.LLM_PROVIDER)
print("PRIMARY_LLM_PROVIDER =", settings.PRIMARY_LLM_PROVIDER)
print("FALLBACK_LLM_PROVIDER =", settings.FALLBACK_LLM_PROVIDER)
print()

answer, used_provider = generate_with_routing(system_prompt, user_prompt)

print("used_provider =", used_provider)
print("[응답]")
print(answer)