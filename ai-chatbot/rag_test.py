from app.services.rag_service import ask_rag


def main():
    query = "세탁기 물이 안 빠져요"

    result = ask_rag(query)

    print(f"질문: {query}")
    print("=" * 60)
    print("답변:")
    print(result["answer"])
    print("=" * 60)
    print("참고 출처:")
    for source in result["sources"]:
        print(source)


if __name__ == "__main__":
    main()