import json
import httpx

from app.core.settings import settings
from app.services.llm_adapters.base import BaseLlmAdapter


class OllamaAdapter(BaseLlmAdapter):
    def _build_payload(self, system_prompt: str, user_prompt: str, stream: bool):
        return {
            "model": settings.OLLAMA_MODEL,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": stream,
            "options": {
                "temperature": settings.OLLAMA_TEMPERATURE,
                "top_p": settings.OLLAMA_TOP_P,
                "num_predict": settings.OLLAMA_NUM_PREDICT,
                "repeat_penalty": settings.OLLAMA_REPEAT_PENALTY
            }
        }

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        with httpx.Client(timeout=settings.LLM_TIMEOUT) as client:
            response = client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=self._build_payload(system_prompt, user_prompt, stream=False)
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    def stream(self, system_prompt: str, user_prompt: str):
        with httpx.stream(
            "POST",
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=self._build_payload(system_prompt, user_prompt, stream=True),
            timeout=settings.LLM_TIMEOUT
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                if isinstance(line, bytes):
                    line = line.decode("utf-8")

                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token