from app.services.hybrid_retrieval_service import hybrid_search

query = "TV 화면이 안 나와요"

results = hybrid_search(query, limit=10)

print("질문:", query)
print("결과 수:", len(results))
print()

for idx, item in enumerate(results, start=1):
    print("-----")
    print("순위:", idx)
    print("source:", item["source"])
    print("chunk_index:", item["chunk_index"])
    print("vector_rank:", item.get("vector_rank"))
    print("keyword_rank:", item.get("keyword_rank"))
    print("rrf_score:", item.get("rrf_score"))
    print("content preview:")
    print(item["content"][:300])
    print()