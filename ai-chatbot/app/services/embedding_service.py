from openai import OpenAI
from app.core.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding