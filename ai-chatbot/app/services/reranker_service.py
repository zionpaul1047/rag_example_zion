from sentence_transformers import CrossEncoder
from app.core.settings import settings

_reranker_model = None


def get_reranker():
    global _reranker_model

    if _reranker_model is None:
        _reranker_model = CrossEncoder(settings.RERANKER_MODEL)

    return _reranker_model


def rerank_documents(query: str, documents: list[dict], top_n: int | None = None) -> list[dict]:
    if not documents:
        return []

    reranker = get_reranker()
    rerank_limit = top_n or settings.TOP_N_RERANK

    pairs = []
    for doc in documents:
        pairs.append((query, doc["content"]))

    scores = reranker.predict(pairs)

    rescored = []
    for doc, score in zip(documents, scores):
        item = dict(doc)
        item["rerank_score"] = float(score)
        rescored.append(item)

    rescored.sort(key=lambda x: x["rerank_score"], reverse=True)

    return rescored[:rerank_limit]