import requests

BASE_URL = "http://127.0.0.1:8000"


def test_approve():
    print("=== 관리자 문서 승인 테스트 ===")
    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/1/approve",
        data={"approved_by": "admin"},
        timeout=60
    )
    print("status:", res.status_code)
    print(res.json())
    print()


def test_index():
    print("=== 관리자 문서 인덱싱 테스트 ===")
    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/1/index",
        timeout=120
    )
    print("status:", res.status_code)
    print(res.json())
    print()


def test_list():
    print("=== 관리자 문서 목록 확인 ===")
    res = requests.get(
        f"{BASE_URL}/admin/rag-documents",
        timeout=60
    )
    print("status:", res.status_code)
    print(res.json())
    print()


if __name__ == "__main__":
    test_approve()
    test_index()
    test_list()