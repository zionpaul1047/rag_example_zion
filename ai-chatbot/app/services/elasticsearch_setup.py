from elasticsearch import Elasticsearch
from app.core.settings import settings


INDEX_NAME = "documents"


def create_index():
    es = Elasticsearch(settings.ELASTICSEARCH_HOST, request_timeout=30)

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)

    es.indices.create(
        index=INDEX_NAME,
        body={
            "mappings": {
                "properties": {
                    "source": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "content": {"type": "text"}
                }
            }
        }
    )

    print(f"[Elasticsearch] 인덱스 생성 완료: {INDEX_NAME}")