from app.services.elasticsearch_search_service import search_by_keyword


def main():
    query = "반품은 며칠 안에 가능한가요"

    results = search_by_keyword(query, limit=3)

    print(f"질문: {query}")
    print("=" * 60)

    for i, result in enumerate(results, start=1):
        print(f"[결과 {i}]")
        print("파일:", result["source"])
        print("청크 번호:", result["chunk_index"])
        print("점수:", result["score"])
        print("내용:")
        print(result["content"])
        print("-" * 60)


if __name__ == "__main__":
    main()