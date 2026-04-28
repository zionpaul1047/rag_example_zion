from app.services.rag_service import ask_rag

cases = [
    "TV 화면이 안 나와요",
    "모니터는 셋톱박스에 어떻게 연결하면되나요?",
    "이 문서에 없는 완전히 이상한 질문입니다. 화성 감자 농장 세금 규정 알려줘",
]

for question in cases:
    print("\n==============================")
    print("질문:", question)

    result = ask_rag(
        question,
        llm_provider="openai",
    )

    print("conversation_id:", result.get("conversation_id"))
    print("eval_result:", result.get("eval_result"))
    print("retry_count:", result.get("retry_count"))
    print("used_provider:", result.get("used_provider"))
    print("metadata:", result.get("metadata"))
    print("sources_count:", len(result.get("sources", [])))
    print("answer:", result.get("answer", "")[:500])