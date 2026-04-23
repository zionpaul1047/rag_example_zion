import requests

BASE_URL = "http://127.0.0.1:8000"


def ping_chat():
    payload = {
        "message": "TV 화면이 안 나와요",
        "stream": False
    }

    res = requests.post(f"{BASE_URL}/chat", json=payload, timeout=300)
    print("chat status:", res.status_code)
    print(res.json())
    print()


def list_session_files():
    res = requests.get(
        f"{BASE_URL}/session-files",
        params={"conversation_id": 19},
        timeout=60
    )
    print("session-files status:", res.status_code)
    print(res.json())
    print()


def list_managed_documents():
    res = requests.get(
        f"{BASE_URL}/admin/rag-documents",
        timeout=60
    )
    print("managed-documents status:", res.status_code)
    print(res.json())
    print()


if __name__ == "__main__":
    ping_chat()
    list_session_files()
    list_managed_documents()