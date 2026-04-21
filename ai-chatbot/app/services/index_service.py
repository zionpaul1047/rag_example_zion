import psycopg
from pgvector.psycopg import register_vector
from app.core.settings import settings
from app.services.document_loader import load_text_documents
from app.services.chunker import split_documents
from app.services.embedding_service import embed_text


def index_documents():
    docs = load_text_documents()
    chunks = split_documents(docs)

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
        for chunk in chunks:
            embedding = embed_text(chunk["content"])

            cur.execute(
                """
                INSERT INTO documents (source, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    chunk["source"],
                    chunk["chunk_index"],
                    chunk["content"],
                    embedding
                )
            )

    conn.close()

    return len(chunks)