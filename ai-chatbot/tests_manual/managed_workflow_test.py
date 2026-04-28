import requests

BASE_URL = "http://127.0.0.1:8000"


def list_docs():
    res = requests.get(f"{BASE_URL}/admin/rag-documents", timeout=60)
    print("list:", res.status_code)
    data = res.json()
    print(data[:3])
    print()
    return data


def request_review(document_id):
    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/{document_id}/request-review",
        timeout=60,
    )
    print("request-review:", res.status_code)
    print(res.json())
    print()


def approve(document_id):
    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/{document_id}/approve",
        data={"approved_by": "admin"},
        timeout=60,
    )
    print("approve:", res.status_code)
    print(res.json())
    print()


def index(document_id):
    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/{document_id}/index",
        timeout=300,
    )
    print("index:", res.status_code)
    print(res.json())
    print()


def retire(document_id):
    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/{document_id}/retire",
        timeout=60,
    )
    print("retire:", res.status_code)
    print(res.json())
    print()


if __name__ == "__main__":
    docs = list_docs()

    target = None
    for doc in docs:
        if doc["status"] == "parsed":
            target = doc
            break

    if not target:
        print("parsed 상태 문서가 없습니다. 관리자 화면에서 문서 업로드 후 처리까지 먼저 진행하세요.")
        raise SystemExit

    doc_id = target["id"]

    request_review(doc_id)
    approve(doc_id)
    index(doc_id)
    retire(doc_id)

    list_docs()