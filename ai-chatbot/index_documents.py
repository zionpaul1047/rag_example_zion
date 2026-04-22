from app.services.db_setup import setup_vector_table
from app.services.index_service import index_documents
from app.services.elasticsearch_index_service import index_to_elasticsearch


def main():
    print("1. PostgreSQL vector 테이블 준비 시작")
    setup_vector_table()
    print("2. PostgreSQL vector 테이블 준비 완료")

    print("3. PostgreSQL 인덱싱 시작")
    pg_count = index_documents()
    print(f"4. PostgreSQL 인덱싱 완료 - 저장된 청크 수: {pg_count}")

    print("5. Elasticsearch 인덱싱 시작")
    es_count = index_to_elasticsearch()
    print(f"6. Elasticsearch 인덱싱 완료 - 저장된 청크 수: {es_count}")


if __name__ == "__main__":
    main()