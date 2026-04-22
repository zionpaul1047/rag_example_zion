import psycopg
from psycopg import sql
from pgvector.psycopg import register_vector

from app.core.settings import settings
from app.services.document_loader import load_documents
from app.services.chunker import split_documents
from app.services.embedding_service import embed_texts


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def index_documents() -> int:
    docs = load_documents(settings.RAW_DOCS_DIR)
    chunks = split_documents(docs)

    if not chunks:
        return 0

    texts = [chunk["content"] for chunk in chunks]
    embeddings = embed_texts(texts, is_query=False)

    records = []
    for chunk, embedding in zip(chunks, embeddings):
        records.append((
            chunk["source"],
            chunk["chunk_index"],
            chunk["content"],
            embedding
        ))

    conn = psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        autocommit=True
    )

    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    register_vector(conn)

    with conn.cursor() as cur:
        for batch in chunked(records, settings.PG_INSERT_BATCH_SIZE):
            values_sql = ",".join(["(%s, %s, %s, %s)"] * len(batch))
            flat_params = []
            for row in batch:
                flat_params.extend(row)

            cur.execute(
                f"""
                INSERT INTO documents (source, chunk_index, content, embedding)
                VALUES {values_sql}
                """,
                flat_params
            )

    conn.close()
    return len(chunks)