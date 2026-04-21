import psycopg
from app.core.settings import settings


def main():
    conn = psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )

    with conn.cursor() as cur:
        cur.execute("SELECT id, source, chunk_index, left(content, 80) FROM documents ORDER BY id;")
        rows = cur.fetchall()

    conn.close()

    print(f"총 행 수: {len(rows)}")
    print("-" * 50)

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()