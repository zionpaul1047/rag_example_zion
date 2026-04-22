import psycopg
from app.core.settings import settings


def setup_vector_table():
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

        cur.execute("DROP TABLE IF EXISTS documents;")

        cur.execute(
            """
            CREATE TABLE documents (
                id BIGSERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                chunk_index INT NOT NULL,
                content TEXT NOT NULL,
                embedding VECTOR(1024)
            )
            """
        )

        cur.execute(
            """
            CREATE INDEX documents_embedding_hnsw_idx
            ON documents
            USING hnsw (embedding vector_cosine_ops)
            """
        )

    conn.close()