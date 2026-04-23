import base64
from pathlib import Path
from openai import OpenAI

from app.core.settings import settings

_client = None


def _get_openai_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _guess_mime_type(file_path: Path) -> str:
    ext = file_path.suffix.lower()

    if ext == ".png":
        return "image/png"
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return "application/octet-stream"


def _to_data_url(file_path: Path) -> str:
    mime_type = _guess_mime_type(file_path)
    image_bytes = file_path.read_bytes()
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def analyze_image_with_vision(file_path: str) -> str:
    if not settings.VISION_ENABLED:
        return ""

    if settings.VISION_PROVIDER.lower() != "openai":
        return ""

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"이미지 파일이 존재하지 않습니다: {file_path}")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > settings.VISION_MAX_IMAGE_SIZE_MB:
        raise ValueError(
            f"비전 분석 가능 최대 크기({settings.VISION_MAX_IMAGE_SIZE_MB}MB)를 초과했습니다."
        )

    client = _get_openai_client()
    image_data_url = _to_data_url(path)

    response = client.chat.completions.create(
        model=settings.OPENAI_VISION_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 TV/가전 화면 상태를 요약하는 분석기입니다. "
                    "반드시 한국어로만, 2~4문장 이내로 간단히 요약하세요. "
                    "화면에 보이는 오류 팝업, 버튼, 핵심 문구, 장치 상태를 설명하세요. "
                    "추측은 하지 말고 화면에서 보이는 것만 말하세요."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이 이미지 화면을 보고 핵심 상태를 요약해 주세요."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        }
                    }
                ]
            }
        ],
        timeout=settings.LLM_TIMEOUT
    )

    return (response.choices[0].message.content or "").strip()