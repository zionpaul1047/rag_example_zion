from app.core.settings import settings


def reciprocal_rank_fusion(
    vector_results: list[dict],
    keyword_results: list[dict],
    limit: int = 10
) -> list[dict]:
    merged = {}
    rrf_k = settings.RRF_K

    # vector 결과 반영
    for rank, item in enumerate(vector_results, start=1):
        key = (item["source"], item["chunk_index"])
        rrf_score = settings.HYBRID_VECTOR_WEIGHT * (1 / (rrf_k + rank))

        if key not in merged:
            merged[key] = {
                "source": item["source"],
                "chunk_index": item["chunk_index"],
                "content": item["content"],
                "vector_rank": rank,
                "keyword_rank": None,
                "rrf_score": 0.0
            }

        merged[key]["rrf_score"] += rrf_score

    # keyword(BM25 역할) 결과 반영
    for rank, item in enumerate(keyword_results, start=1):
        key = (item["source"], item["chunk_index"])
        rrf_score = settings.HYBRID_KEYWORD_WEIGHT * (1 / (rrf_k + rank))

        if key not in merged:
            merged[key] = {
                "source": item["source"],
                "chunk_index": item["chunk_index"],
                "content": item["content"],
                "vector_rank": None,
                "keyword_rank": rank,
                "rrf_score": 0.0
            }
        else:
            merged[key]["keyword_rank"] = rank

        merged[key]["rrf_score"] += rrf_score

    fused = list(merged.values())
    fused.sort(key=lambda x: x["rrf_score"], reverse=True)

    return fused[:limit]