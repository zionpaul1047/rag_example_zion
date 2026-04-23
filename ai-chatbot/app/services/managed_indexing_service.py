import psycopg
from pgvector.psycopg import register_vector
from elasticsearch import Elasticsearch, helpers

from app.core.settings import settings
from app.services.document_registry_service import (
    get_managed_document,
    mark_managed_document_indexed
)
from app.services.chunker import split_documents
from app.services.embedding_service import embed_texts
from app.services.elasticsearch_index_service import INDEX_NAME


def index_managed_document(document_id: int) -> dict:
    document = get_managed_document(document_id)
    if not document:
        raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

    parsed_text = (document.get("parsed_text") or "").strip()
    if not parsed_text:
        raise ValueError("parsed_text가 없습니다. 먼저 process를 수행하세요.")

    docs = [
        {
            "source": document["original_name"],
            "content": parsed_text,
            "file_type": document.get("file_extension", "").lstrip(".") or "managed"
        }
    ]

    chunks = split_documents(docs)
    if not chunks:
        raise ValueError("청킹 결과가 없습니다.")

    texts = [chunk["content"] for chunk in chunks]
    embeddings = embed_texts(texts, is_query=False)

    conn = psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        autocommit=True
    )
    register_vector(conn)

    with conn.cursor() as cur:
        for chunk, embedding in zip(chunks, embeddings):
            cur.execute(
                """
                INSERT INTO documents (source, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    f"[managed]{chunk['source']}",
                    chunk["chunk_index"],
                    chunk["content"],
                    embedding
                )
            )

    conn.close()

    es = Elasticsearch(settings.ELASTICSEARCH_HOST, request_timeout=30)

    actions = []
    for chunk in chunks:
        actions.append({
            "_index": INDEX_NAME,
            "_source": {
                "source": f"[managed]{chunk['source']}",
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"]
            }
        })

    if actions:
        helpers.bulk(es, actions)

    mark_managed_document_indexed(document_id)

    return {
        "document_id": document_id,
        "status": "indexed",
        "chunk_count": len(chunks),
        "source": document["original_name"]
    }