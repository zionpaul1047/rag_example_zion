from app.services.rag_service import ask_rag

conversation_id = 19
query = "업로드한 파일 기준으로 TV 화면이 안 나올 때 어떻게 해야 해?"

result = ask_rag(query, conversation_id=conversation_id)

print("conversation_id:", result["conversation_id"])
print("used_provider:", result.get("used_provider"))
print()
print("[답변]")
print(result["answer"])
print()
print("[출처]")
for src in result["sources"]:
    print(src)