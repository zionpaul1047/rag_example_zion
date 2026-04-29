from app.services.rag_service import ask_rag

questions = [
    "TV 화면이 안 나와요",
    "그럼 다음은?",
    "화성 감자 농장 세금 규정 알려줘",
]

conversation_id = None

for q in questions:
    print("\n===================")
    print("질문:", q)

    result = ask_rag(
        q,
        conversation_id=conversation_id,
        llm_provider="openai",
    )

    conversation_id = result["conversation_id"]

    print("conversation_id:", result.get("conversation_id"))
    print("graph:", result.get("graph"))
    print("eval_result:", result.get("eval_result"))
    print("retry_count:", result.get("retry_count"))
    print("used_provider:", result.get("used_provider"))
    print("metadata:", result.get("metadata"))
    print("sources:", result.get("sources"))
    print("answer:", result.get("answer", "")[:500])
    print("graph_trace:", result.get("graph_trace"))