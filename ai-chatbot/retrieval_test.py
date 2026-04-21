from app.services.retrieval_service import search_similar_documents


def main():
    query = "세탁기 물이 안 빠져요"

    results = search_similar_documents(query, limit=3)

    print(f"질문: {query}")
    print("=" * 60)

    for i, result in enumerate(results, start=1):
        print(f"[결과 {i}]")
        print(f"문서: {result['source']}")
        print(f"청크 번호: {result['chunk_index']}")
        print(f"거리: {result['distance']}")
        print("내용:")
        print(result["content"])
        print("-" * 60)


if __name__ == "__main__":
    main()