from app.services.elasticsearch_search_service import search_by_keyword


def search_bm25(query: str, limit: int = 10) -> list[dict]:
    """
    현재 단계에서는 Elasticsearch 검색 결과를
    BM25 역할의 lexical search 결과로 사용한다.
    """
    results = search_by_keyword(query, limit=limit)

    normalized = []
    for rank, item in enumerate(results, start=1):
        normalized.append({
            "source": item["source"],
            "chunk_index": item["chunk_index"],
            "content": item["content"],
            "score": float(item.get("score", 0.0)),
            "rank": rank,
            "search_type": "bm25"
        })

    return normalized