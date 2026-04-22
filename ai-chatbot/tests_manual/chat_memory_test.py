from app.services.rag_service import ask_rag

print("1차 질문")
result1 = ask_rag("TV 화면이 안 나와요")

conversation_id = result1["conversation_id"]

print("conversation_id:", conversation_id)
print(result1["answer"])
print()

print("2차 질문")
result2 = ask_rag(
    "HDMI는 연결했어요. 그 다음엔?",
    conversation_id=conversation_id
)

print(result2["answer"])
print()