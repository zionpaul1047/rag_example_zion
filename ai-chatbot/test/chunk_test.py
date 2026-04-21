from app.services.document_loader import load_text_documents
from app.services.chunker import split_documents


def main():
    docs = load_text_documents()
    chunks = split_documents(docs)

    print("총 청크 수:", len(chunks))
    print("-" * 50)

    for i, chunk in enumerate(chunks[:10], start=1):
        print(f"[Chunk {i}]")
        print("파일:", chunk["source"])
        print("번호:", chunk["chunk_index"])
        print(chunk["content"])
        print("-" * 50)


if __name__ == "__main__":
    main()