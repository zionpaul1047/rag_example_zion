import requests

BASE_URL = "http://127.0.0.1:8000"


def login():
    res = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "zion",
            "password": "user1234",
        },
        timeout=60,
    )
    print("login status:", res.status_code)
    data = res.json()
    print(data)
    print()
    return data["access_token"]


def list_conversations(token):
    res = requests.get(
        f"{BASE_URL}/conversations",
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=60,
    )
    print("list status:", res.status_code)
    data = res.json()
    print(data)
    print()
    return data


def get_messages(token, conversation_id):
    res = requests.get(
        f"{BASE_URL}/conversations/{conversation_id}/messages",
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=60,
    )
    print("messages status:", res.status_code)
    print(res.json())
    print()


if __name__ == "__main__":
    token = login()
    conversations = list_conversations(token)

    if conversations:
        get_messages(token, conversations[0]["id"])