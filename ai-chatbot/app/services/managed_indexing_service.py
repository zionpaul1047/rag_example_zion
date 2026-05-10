import psycopg
from pgvector.psycopg import register_vector
from elasticsearch import Elasticsearch, helpers

from app.core.settings import settings
from app.services.document_registry_service import (
    get_managed_document,
    activate_managed_document,
)
from app.services.chunker import split_documents
from app.services.embedding_service import embed_texts
from app.services.elasticsearch_index_service import INDEX_NAME


def managed_source(document_id: int, original_name: str) -> str:
    return f"[managed:{document_id}]{original_name}"


def delete_existing_vector_chunks(conn, source: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM documents WHERE source = %s",
            (source,),
        )
        return cur.rowcount


def delete_existing_keyword_chunks(es: Elasticsearch, source: str) -> int:
    response = es.delete_by_query(
        index=INDEX_NAME,
        query={
            "term": {
                "source": source,
            }
        },
        conflicts="proceed",
        refresh=True,
    )
    return int(response.get("deleted", 0))


def index_managed_document(document_id: int) -> dict:
    document = get_managed_document(document_id)
    if not document:
        raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

    parsed_text = (document.get("parsed_text") or "").strip()
    if not parsed_text:
        raise ValueError("parsed_text가 없습니다. 먼저 process를 실행하세요.")

    source = managed_source(document_id, document["original_name"])

    docs = [
        {
            "source": document["original_name"],
            "content": parsed_text,
            "file_type": document.get("file_extension", "").lstrip(".") or "managed",
        }
    ]

    chunks = split_documents(docs)
    if not chunks:
        raise ValueError("청크 결과가 없습니다.")

    texts = [chunk["content"] for chunk in chunks]
    embeddings = embed_texts(texts, is_query=False)

    conn = psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        autocommit=True,
    )
    register_vector(conn)

    vector_deleted = delete_existing_vector_chunks(conn, source)

    with conn.cursor() as cur:
        for chunk, embedding in zip(chunks, embeddings):
            cur.execute(
                """
                INSERT INTO documents (source, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    source,
                    chunk["chunk_index"],
                    chunk["content"],
                    embedding,
                ),
            )

    conn.close()

    es = Elasticsearch(settings.ELASTICSEARCH_HOST, request_timeout=30)
    keyword_deleted = delete_existing_keyword_chunks(es, source)

    actions = []
    for chunk in chunks:
        actions.append({
            "_index": INDEX_NAME,
            "_source": {
                "source": source,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
            },
        })

    if actions:
        helpers.bulk(es, actions)

    activate_managed_document(document_id)

    return {
        "document_id": document_id,
        "status": "indexed",
        "chunk_count": len(chunks),
        "source": document["original_name"],
        "managed_source": source,
        "vector_deleted": vector_deleted,
        "keyword_deleted": keyword_deleted,
    }
