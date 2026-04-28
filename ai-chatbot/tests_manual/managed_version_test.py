import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

TEST_FILE = Path("data/samples/samsung_faq.txt")


def list_docs():
    res = requests.get(f"{BASE_URL}/admin/rag-documents", timeout=60)
    print("list:", res.status_code)
    data = res.json()

    for doc in data[:5]:
        print({
            "id": doc["id"],
            "title": doc["title"],
            "version": doc.get("version"),
            "status": doc.get("status"),
            "document_key": doc.get("document_key"),
            "is_active": doc.get("is_active"),
            "parent_document_id": doc.get("parent_document_id"),
        })

    print()
    return data


def upload_new_version(parent_id: int):
    if not TEST_FILE.exists():
        raise FileNotFoundError(f"테스트 파일 없음: {TEST_FILE}")

    with TEST_FILE.open("rb") as f:
        res = requests.post(
            f"{BASE_URL}/admin/rag-documents/{parent_id}/versions/upload",
            files={"file": (TEST_FILE.name, f, "text/plain")},
            timeout=60,
        )

    print("upload version:", res.status_code)
    print(res.json())
    print()


if __name__ == "__main__":
    docs = list_docs()

    target = None
    for doc in docs:
        if doc.get("is_active") == 1:
            target = doc
            break

    if not target:
        print("is_active=1 문서가 없습니다. 먼저 indexed 활성 문서를 만들어주세요.")
        raise SystemExit

    upload_new_version(target["id"])

    list_docs()