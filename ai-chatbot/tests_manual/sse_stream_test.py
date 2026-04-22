import json
import requests

url = "http://127.0.0.1:8000/chat"

payload = {
    "message": "TV 화면이 안 나와요",
    "stream": True
}

with requests.post(url, json=payload, stream=True) as response:
    response.raise_for_status()

    print("=== SSE 응답 시작 ===")
    for line in response.iter_lines():
        if not line:
            continue

        decoded = line.decode("utf-8")
        if decoded.startswith("data: "):
            data = decoded[6:]
            item = json.loads(data)
            print(item)
    print("=== SSE 응답 종료 ===")