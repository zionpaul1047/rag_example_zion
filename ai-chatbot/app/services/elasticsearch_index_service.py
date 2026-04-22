from elasticsearch import Elasticsearch, helpers

from app.core.settings import settings
from app.services.document_loader import load_documents
from app.services.chunker import split_documents

INDEX_NAME = "documents"


def batch_iter(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def index_to_elasticsearch() -> int:
    es = Elasticsearch(settings.ELASTICSEARCH_HOST, request_timeout=30)

    docs = load_documents(settings.RAW_DOCS_DIR)
    chunks = split_documents(docs)

    if not chunks:
        return 0

    actions = []
    for chunk in chunks:
        actions.append({
            "_index": INDEX_NAME,
            "_source": {
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"]
            }
        })

    for batch in batch_iter(actions, settings.ES_BULK_BATCH_SIZE):
        helpers.bulk(es, batch)

    print(f"[Elasticsearch] 저장 완료 - 청크 수: {len(chunks)}")
    return len(chunks)