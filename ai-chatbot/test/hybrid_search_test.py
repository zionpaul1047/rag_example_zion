from app.services.hybrid_retrieval_service import hybrid_search


def main():
    query = "세탁기 물이 안 빠져요"

    results = hybrid_search(query, limit=5)

    print(f"질문: {query}")
    print("=" * 60)

    for i, result in enumerate(results, start=1):
        print(f"[결과 {i}]")
        print("파일:", result["source"])
        print("청크 번호:", result["chunk_index"])
        print("vector_score:", result["vector_score"])
        print("keyword_score:", result["keyword_score"])
        print("final_score:", result["final_score"])
        print("내용:")
        print(result["content"])
        print("-" * 60)


if __name__ == "__main__":
    main()