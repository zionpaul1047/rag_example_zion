from typing import List
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from app.core.settings import settings

_openai_client = None
_bge_model = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _get_bge_model():
    global _bge_model
    if _bge_model is None:
        _bge_model = SentenceTransformer(settings.BGE_MODEL_NAME)
    return _bge_model


def embed_text(text: str, is_query: bool = False) -> List[float]:
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "openai":
        client = _get_openai_client()
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    if provider == "bge":
        model = _get_bge_model()
        if is_query:
            embedding = model.encode_query(text, normalize_embeddings=True)
        else:
            embedding = model.encode_document(text, normalize_embeddings=True)
        return embedding.tolist()

    raise ValueError(f"지원하지 않는 EMBEDDING_PROVIDER 입니다: {settings.EMBEDDING_PROVIDER}")


def embed_texts(texts: list[str], is_query: bool = False) -> list[list[float]]:
    provider = settings.EMBEDDING_PROVIDER.lower()

    if not texts:
        return []

    if provider == "openai":
        client = _get_openai_client()
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]

    if provider == "bge":
        model = _get_bge_model()
        batch_size = settings.EMBEDDING_BATCH_SIZE

        if is_query:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True
            )
        else:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True
            )

        return embeddings.tolist()

    raise ValueError(f"지원하지 않는 EMBEDDING_PROVIDER 입니다: {settings.EMBEDDING_PROVIDER}")