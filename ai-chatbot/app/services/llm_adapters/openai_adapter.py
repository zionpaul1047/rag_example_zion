from openai import OpenAI
from app.core.settings import settings
from app.services.llm_adapters.base import BaseLlmAdapter


class OpenAiAdapter(BaseLlmAdapter):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            timeout=settings.LLM_TIMEOUT
        )

        return response.choices[0].message.content or ""

    def stream(self, system_prompt: str, user_prompt: str):
        stream = self.client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True,
            timeout=settings.LLM_TIMEOUT
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta