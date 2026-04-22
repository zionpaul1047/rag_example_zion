from app.services.hybrid_retrieval_service import hybrid_search
from app.services.reranker_service import rerank_documents

query = "TV 화면이 안 나와요"

hybrid_results = hybrid_search(query, limit=10)
reranked_results = rerank_documents(query, hybrid_results, top_n=5)

print("질문:", query)
print("hybrid 후보 수:", len(hybrid_results))
print("rerank 결과 수:", len(reranked_results))
print()

for idx, item in enumerate(reranked_results, start=1):
    print("-----")
    print("순위:", idx)
    print("source:", item["source"])
    print("chunk_index:", item["chunk_index"])
    print("vector_rank:", item.get("vector_rank"))
    print("keyword_rank:", item.get("keyword_rank"))
    print("rrf_score:", item.get("rrf_score"))
    print("rerank_score:", item.get("rerank_score"))
    print("content preview:")
    print(item["content"][:300])
    print()