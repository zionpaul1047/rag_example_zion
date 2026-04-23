import requests

BASE_URL = "http://127.0.0.1:8000"


def test_upload_image_auto_process():
    print("=== 이미지 업로드 + OCR + 비전 분석 테스트 ===")

    image_path = "data/raw_docs/sample_tv_error.png"

    with open(image_path, "rb") as f:
        files = {
            "file": ("sample_tv_error.png", f, "image/png")
        }
        data = {
            "conversation_id": 19,
            "user_id": "zion"
        }

        res = requests.post(
            f"{BASE_URL}/session-files/upload",
            files=files,
            data=data,
            timeout=300
        )

    print("upload status:", res.status_code)
    print(res.json())
    print()


def test_list_session_files():
    print("=== 세션 파일 목록 확인 ===")

    res = requests.get(
        f"{BASE_URL}/session-files",
        params={"conversation_id": 19},
        timeout=60
    )

    print("list status:", res.status_code)
    data = res.json()

    for item in data[:3]:
        print("-----")
        print("id:", item["id"])
        print("original_name:", item["original_name"])
        print("doc_status:", item["doc_status"])
        print("ocr_text:", item.get("ocr_text"))
        print("vision_summary:", item.get("vision_summary"))
        print("parsed_text:", item.get("parsed_text"))
        print()

if __name__ == "__main__":
    test_upload_image_auto_process()
    test_list_session_files()