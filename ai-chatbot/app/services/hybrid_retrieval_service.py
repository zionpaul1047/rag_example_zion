from app.services.retrieval_service import search_similar_documents
from app.services.elasticsearch_search_service import search_by_keyword


def hybrid_search(query: str, limit: int = 5):
    vector_results = search_similar_documents(query, limit=5)
    keyword_results = search_by_keyword(query, limit=5)

    merged = {}

    # 1. pgvector 결과 반영
    for item in vector_results:
        key = (item["source"], item["chunk_index"])

        vector_score = 1 / (1 + item["distance"])

        merged[key] = {
            "source": item["source"],
            "chunk_index": item["chunk_index"],
            "content": item["content"],
            "vector_score": vector_score,
            "keyword_score": 0.0,
            "final_score": vector_score
        }

    # 2. Elasticsearch 결과 반영
    for item in keyword_results:
        key = (item["source"], item["chunk_index"])

        keyword_score = float(item["score"])

        if key in merged:
            merged[key]["keyword_score"] = keyword_score
            merged[key]["final_score"] = (
                merged[key]["vector_score"] + keyword_score
            )
        else:
            merged[key] = {
                "source": item["source"],
                "chunk_index": item["chunk_index"],
                "content": item["content"],
                "vector_score": 0.0,
                "keyword_score": keyword_score,
                "final_score": keyword_score
            }

    # 3. 정렬
    results = list(merged.values())
    results.sort(key=lambda x: x["final_score"], reverse=True)

    return results[:limit]