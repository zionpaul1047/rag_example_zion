from app.core.settings import settings

RRFKey = tuple[str, int]

REQUIRED_RESULT_FIELDS = ("source", "chunk_index", "content")


def _validate_result_item(item: dict, search_type: str) -> None:
    missing_fields = [
        field
        for field in REQUIRED_RESULT_FIELDS
        if field not in item
    ]

    if missing_fields:
        fields = ", ".join(missing_fields)
        raise ValueError(f"{search_type} result is missing required field(s): {fields}")


def _result_key(item: dict) -> RRFKey:
    return item["source"], item["chunk_index"]


def _create_fused_item(item: dict, rank_field: str, rank: int) -> dict:
    return {
        "source": item["source"],
        "chunk_index": item["chunk_index"],
        "content": item["content"],
        "vector_rank": rank if rank_field == "vector_rank" else None,
        "keyword_rank": rank if rank_field == "keyword_rank" else None,
        "rrf_score": 0.0,
    }


def _apply_ranked_results(
    merged: dict[RRFKey, dict],
    results: list[dict],
    *,
    search_type: str,
    rank_field: str,
    weight: float,
    rrf_k: int,
) -> None:
    for rank, item in enumerate(results, start=1):
        _validate_result_item(item, search_type)

        key = _result_key(item)
        rrf_score = weight * (1 / (rrf_k + rank))

        if key not in merged:
            merged[key] = _create_fused_item(item, rank_field, rank)
        else:
            merged[key][rank_field] = rank

        merged[key]["rrf_score"] += rrf_score


def reciprocal_rank_fusion(
    vector_results: list[dict],
    keyword_results: list[dict],
    limit: int = 10
) -> list[dict]:
    merged: dict[RRFKey, dict] = {}
    rrf_k = settings.RRF_K

    _apply_ranked_results(
        merged,
        vector_results,
        search_type="vector",
        rank_field="vector_rank",
        weight=settings.HYBRID_VECTOR_WEIGHT,
        rrf_k=rrf_k,
    )
    _apply_ranked_results(
        merged,
        keyword_results,
        search_type="keyword",
        rank_field="keyword_rank",
        weight=settings.HYBRID_KEYWORD_WEIGHT,
        rrf_k=rrf_k,
    )

    fused = list(merged.values())
    fused.sort(key=lambda x: x["rrf_score"], reverse=True)

    return fused[:limit]
