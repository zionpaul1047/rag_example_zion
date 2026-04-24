import requests

BASE_URL = "http://127.0.0.1:8000"


def login_admin():
    res = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "admin",
            "password": "admin1234",
        },
        timeout=60,
    )
    print("login status:", res.status_code)
    data = res.json()
    print(data)
    print()
    return data["access_token"]


def dashboard_summary(token):
    res = requests.get(
        f"{BASE_URL}/admin/dashboard/summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=60,
    )

    print("summary status:", res.status_code)
    print(res.json())


if __name__ == "__main__":
    token = login_admin()
    dashboard_summary(token)