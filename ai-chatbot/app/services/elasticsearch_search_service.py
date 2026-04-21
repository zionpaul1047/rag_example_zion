from elasticsearch import Elasticsearch
from app.core.settings import settings

INDEX_NAME = "documents"


def search_by_keyword(query: str, limit: int = 3):
    es = Elasticsearch(settings.ELASTICSEARCH_HOST, request_timeout=30)

    response = es.search(
        index=INDEX_NAME,
        query={
            "match": {
                "content": query
            }
        },
        size=limit
    )

    results = []

    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "source": source["source"],
            "chunk_index": source["chunk_index"],
            "content": source["content"],
            "score": hit["_score"]
        })

    return results