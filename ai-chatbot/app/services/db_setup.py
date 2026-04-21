import psycopg
from pgvector.psycopg import register_vector
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

    register_vector(conn)

    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS documents;
        """)

        cur.execute("""
            CREATE TABLE documents (
                id bigserial PRIMARY KEY,
                source text NOT NULL,
                chunk_index integer NOT NULL,
                content text NOT NULL,
                embedding vector(1536) NOT NULL
            );
        """)

    conn.close()