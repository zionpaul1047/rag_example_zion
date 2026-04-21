import psycopg
from app.core.settings import settings
from app.services.embedding_service import embed_text


def search_similar_documents(query: str, limit: int = 3):
    query_embedding = embed_text(query)

    conn = psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                source,
                chunk_index,
                content,
                embedding <-> %s::vector AS distance
            FROM documents
            ORDER BY embedding <-> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, limit)
        )

        rows = cur.fetchall()

    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "source": row[1],
            "chunk_index": row[2],
            "content": row[3],
            "distance": row[4]
        })

    return results