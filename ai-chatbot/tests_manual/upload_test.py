import requests

BASE_URL = "http://127.0.0.1:8000"


def test_session_upload():
    print("=== 사용자 세션 파일 업로드 테스트 ===")

    with open("data/raw_docs/samsung_faq.txt", "rb") as f:
        files = {
            "file": ("samsung_faq.txt", f, "text/plain")
        }

        data = {
            "conversation_id": 19,
            "user_id": "zion"
        }

        res = requests.post(
            f"{BASE_URL}/session-files/upload",
            files=files,
            data=data,
            timeout=60
        )

    print("status:", res.status_code)
    print(res.json())
    print()


def test_managed_upload():
    print("=== 관리자 문서 업로드 테스트 ===")

    with open("data/raw_docs/samsung_faq.txt", "rb") as f:
        files = {
            "file": ("samsung_faq.txt", f, "text/plain")
        }

        data = {
            "title": "삼성 TV FAQ",
            "category": "tv"
        }

        res = requests.post(
            f"{BASE_URL}/admin/rag-documents/upload",
            files=files,
            data=data,
            timeout=60
        )

    print("status:", res.status_code)
    print(res.json())
    print()


def test_list_files():
    print("=== 세션 파일 목록 ===")

    res = requests.get(
        f"{BASE_URL}/session-files",
        params={"conversation_id": 19},
        timeout=60
    )

    print("status:", res.status_code)
    print(res.json())
    print()


def test_list_managed():
    print("=== 관리자 문서 목록 ===")

    res = requests.get(
        f"{BASE_URL}/admin/rag-documents",
        timeout=60
    )

    print("status:", res.status_code)
    print(res.json())
    print()


if __name__ == "__main__":
    test_session_upload()
    test_managed_upload()
    test_list_files()
    test_list_managed()