from elasticsearch import Elasticsearch
from app.core.settings import settings
from app.services.document_loader import load_text_documents
from app.services.chunker import split_documents

INDEX_NAME = "documents"


def index_to_elasticsearch():
    es = Elasticsearch(settings.ELASTICSEARCH_HOST, request_timeout=30)

    docs = load_text_documents()
    chunks = split_documents(docs)

    for chunk in chunks:
        es.index(
            index=INDEX_NAME,
            document={
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"]
            }
        )

    print(f"[Elasticsearch] 저장 완료 - 청크 수: {len(chunks)}")
    return len(chunks)