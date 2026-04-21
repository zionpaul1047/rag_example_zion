from app.services.elasticsearch_setup import create_index
from app.services.elasticsearch_index_service import index_to_elasticsearch


def main():
    print("1. Elasticsearch 인덱스 생성 시작")
    create_index()

    print("2. 문서 저장 시작")
    count = index_to_elasticsearch()

    print(f"3. 완료 - 저장된 청크 수: {count}")


if __name__ == "__main__":
    main()