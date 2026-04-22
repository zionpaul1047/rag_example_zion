import psycopg
from pgvector.psycopg import register_vector
from app.core.settings import settings
from app.services.embedding_service import embed_text


def search_similar_documents(query: str, limit: int = 10) -> list[dict]:
    query_embedding = embed_text(query, is_query=True)

    conn = psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )

    register_vector(conn)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source, chunk_index, content, embedding <=> %s::vector AS distance
            FROM documents
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, limit)
        )

        rows = cur.fetchall()

    conn.close()

    results = []
    for row in rows:
        results.append({
            "source": row[0],
            "chunk_index": row[1],
            "content": row[2],
            "distance": float(row[3])
        })

    return results