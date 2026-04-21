import psycopg
from elasticsearch import Elasticsearch
from app.core.settings import settings


def check_postgres():
    conn = psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )

    cur = conn.cursor()
    cur.execute("SELECT version();")
    result = cur.fetchone()

    cur.close()
    conn.close()

    return result[0]


def check_elasticsearch():
    es = Elasticsearch(
        settings.ELASTICSEARCH_HOST,
        request_timeout=30
    )

    if es.ping():
        info = es.info()
        return info["version"]["number"]

    return None