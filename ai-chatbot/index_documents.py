from app.services.db_setup import setup_vector_table
from app.services.index_service import index_documents


def main():
    print("1. documents 테이블 준비 시작")
    setup_vector_table()
    print("2. documents 테이블 준비 완료")

    print("3. 문서 인덱싱 시작")
    count = index_documents()
    print(f"4. 인덱싱 완료 - 저장된 청크 수: {count}")


if __name__ == "__main__":
    main()