from app.services.document_loader import load_text_documents


def main():
    documents = load_text_documents()

    print(f"문서 개수: {len(documents)}")
    print("-" * 50)

    for i, doc in enumerate(documents, start=1):
        print(f"[문서 {i}]")
        print(f"파일명: {doc['source']}")
        print("내용 미리보기:")
        print(doc["content"][:200])
        print("-" * 50)


if __name__ == "__main__":
    main()