import os
from dotenv import load_dotenv
import psycopg
from elasticsearch import Elasticsearch


def test_postgres():
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    conn = psycopg.connect(
        host=host,
        port=port,
        dbname=db,
        user=user,
        password=password
    )

    cur = conn.cursor()
    cur.execute("SELECT version();")
    result = cur.fetchone()

    print("[PostgreSQL 연결 성공]")
    print(result[0])

    cur.close()
    conn.close()


def test_elasticsearch():
    es_host = os.getenv("ELASTICSEARCH_HOST")

    try:
        es = Elasticsearch(
            es_host,
            request_timeout=30,
        )

        print("ping 시도 중...")
        print("es_host =", es_host)

        if es.ping():
            print("[Elasticsearch 연결 성공]")
            info = es.info()
            print("Version:", info["version"]["number"])
        else:
            print("[Elasticsearch 응답 없음]")
            print("브라우저에서 http://localhost:9200 접속도 확인해보세요.")
    except Exception as e:
        print("[Elasticsearch 오류]")
        print(type(e).__name__)
        print(e)


if __name__ == "__main__":
    load_dotenv()

    print("환경변수 로드 완료")
    test_postgres()
    test_elasticsearch()