from app.core.settings import settings
from app.services.retrieval_service import search_similar_documents
from app.services.bm25_service import search_bm25
from app.services.rrf_service import reciprocal_rank_fusion


def hybrid_search(query: str, limit: int | None = None) -> list[dict]:
    retrieval_limit = limit or settings.TOP_K_RETRIEVAL

    vector_raw = search_similar_documents(query, limit=retrieval_limit)
    bm25_results = search_bm25(query, limit=retrieval_limit)

    vector_results = []
    for rank, item in enumerate(vector_raw, start=1):
        vector_results.append({
            "source": item["source"],
            "chunk_index": item["chunk_index"],
            "content": item["content"],
            "distance": item.get("distance", 0.0),
            "rank": rank,
            "search_type": "vector"
        })

    fused_results = reciprocal_rank_fusion(
        vector_results=vector_results,
        keyword_results=bm25_results,
        limit=retrieval_limit
    )

    return fused_results