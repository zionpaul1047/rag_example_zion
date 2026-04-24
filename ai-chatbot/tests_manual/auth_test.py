import requests

BASE_URL = "http://127.0.0.1:8000"


def test_login(username: str, password: str):
    print(f"=== 로그인 테스트: {username} ===")

    res = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": username,
            "password": password,
        },
        timeout=60,
    )

    print("status:", res.status_code)
    data = res.json()
    print(data)
    print()

    return data.get("access_token")


def test_me(token: str):
    print("=== me 테스트 ===")

    res = requests.get(
        f"{BASE_URL}/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=60,
    )

    print("status:", res.status_code)
    print(res.json())
    print()


if __name__ == "__main__":
    user_token = test_login("zion", "user1234")
    if user_token:
        test_me(user_token)

    admin_token = test_login("admin", "admin1234")
    if admin_token:
        test_me(admin_token)