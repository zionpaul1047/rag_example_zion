def evaluate_docs(sources: list[dict] | None) -> str:
    """
    반환값:
    - good: 검색 결과가 충분함
    - bad: 결과는 있으나 품질이 낮음
    - no_docs: 검색 결과 없음
    """
    if not sources:
        return "no_docs"

    scores = [
        source.get("rerank_score")
        for source in sources
        if isinstance(source.get("rerank_score"), (int, float))
    ]

    if not scores:
        return "good"

    top_score = max(scores)

    if top_score < 3:
        return "bad"

    return "good"


def build_no_docs_answer(user_message: str) -> str:
    return (
        "현재 등록된 문서에서는 질문과 직접 관련된 내용을 찾지 못했습니다.\n\n"
        "다만 문제를 더 정확히 확인하려면 아래 정보를 추가로 알려주세요.\n"
        "1. 제품 종류 또는 모델명\n"
        "2. 화면에 표시되는 에러 문구\n"
        "3. 발생 상황\n"
        "4. 이미 시도한 조치\n\n"
        f"질문 내용: {user_message}"
    )


def build_retry_query(user_message: str) -> str:
    """
    1차 검색 품질이 낮을 때 사용하는 단순 재검색 쿼리.
    나중에 LLM 기반 query rewrite로 교체 가능.
    """
    base = " ".join(user_message.strip().split())

    hints = [
        "문제",
        "해결",
        "확인",
        "설정",
        "연결",
        "전원",
        "오류",
        "에러",
    ]

    return f"{base} {' '.join(hints)}"