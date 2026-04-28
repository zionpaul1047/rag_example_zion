from app.services.rag_service import ask_rag

print("=== 1차 질문 ===")
result1 = ask_rag(
    "TV 화면이 안 나와요",
    llm_provider="openai",
)

conversation_id = result1["conversation_id"]

print("conversation_id:", conversation_id)
print("answer:", result1["answer"][:300])
print("metadata:", result1.get("metadata"))
print()

print("=== 2차 질문: 애매한 후속 질문 ===")
result2 = ask_rag(
    "그럼 다음은?",
    conversation_id=conversation_id,
    llm_provider="openai",
)

print("conversation_id:", result2["conversation_id"])
print("eval_result:", result2.get("eval_result"))
print("retry_count:", result2.get("retry_count"))
print("metadata:", result2.get("metadata"))
print("answer:", result2["answer"][:500])