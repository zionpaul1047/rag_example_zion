import requests

BASE_URL = "http://127.0.0.1:8000"


def test_process_session_document():
    print("=== 세션 문서 처리 테스트 ===")

    res = requests.post(
        f"{BASE_URL}/session-files/1/process",
        timeout=120
    )

    print("status:", res.status_code)
    print(res.json())
    print()


def test_process_managed_document():
    print("=== 관리자 문서 처리 테스트 ===")

    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/1/process",
        timeout=120
    )

    print("status:", res.status_code)
    print(res.json())
    print()


def test_list_session_after_processing():
    print("=== 처리 후 세션 문서 목록 ===")

    res = requests.get(
        f"{BASE_URL}/session-files",
        params={"conversation_id": 19},
        timeout=60
    )

    print("status:", res.status_code)
    print(res.json())
    print()


def test_list_managed_after_processing():
    print("=== 처리 후 관리자 문서 목록 ===")

    res = requests.get(
        f"{BASE_URL}/admin/rag-documents",
        timeout=60
    )

    print("status:", res.status_code)
    print(res.json())
    print()


if __name__ == "__main__":
    test_process_session_document()
    test_process_managed_document()
    test_list_session_after_processing()
    test_list_managed_after_processing()