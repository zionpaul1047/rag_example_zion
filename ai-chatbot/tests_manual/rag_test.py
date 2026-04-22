from app.services.rag_service import ask_rag

query = "TV 화면이 안 나와요"

result = ask_rag(query)

print("질문:", query)
print("retrieved_count:", result.get("retrieved_count"))
print("reranked_count:", result.get("reranked_count"))
print()
print("[답변]")
print(result["answer"])
print()
print("[출처]")
for source in result["sources"]:
    print(source)