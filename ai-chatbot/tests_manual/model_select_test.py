from app.services.rag_service import ask_rag

for provider in ["auto", "openai", "ollama"]:
    print(f"\n=== provider: {provider} ===")

    result = ask_rag(
        "TV 화면이 안 나와요",
        llm_provider=provider,
    )

    print("conversation_id:", result["conversation_id"])
    print("requested_provider:", result.get("requested_provider"))
    print("used_provider:", result.get("used_provider"))
    print("answer:", result["answer"][:300])