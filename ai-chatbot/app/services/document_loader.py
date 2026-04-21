from pathlib import Path


RAW_DOCS_PATH = Path("data/raw_docs")


def load_text_documents():
    documents = []

    if not RAW_DOCS_PATH.exists():
        print(f"[오류] 폴더가 없습니다: {RAW_DOCS_PATH}")
        return documents

    for file_path in RAW_DOCS_PATH.glob("*.txt"):
        content = file_path.read_text(encoding="utf-8")

        documents.append({
            "source": file_path.name,
            "content": content
        })

    return documents