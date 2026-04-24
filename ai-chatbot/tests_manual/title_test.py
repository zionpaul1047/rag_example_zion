from app.services.rag_service import ask_rag

result = ask_rag(
    "TV 화면이 안 나와요. HDMI 연결도 했습니다.",
    llm_provider="openai"
)

print(result)