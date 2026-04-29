OUT_OF_SCOPE_KEYWORDS = [
    "세금", "세무", "농장", "감자", "화성", "부동산", "주식", "코인",
    "법률", "변호사", "병원", "진단", "처방", "정치", "선거",
]

DOMAIN_KEYWORDS = [
    "삼성", "TV", "티비", "화면", "HDMI", "리모컨", "사운드바",
    "세탁기", "냉장고", "갤럭시", "스마트폰", "에러", "오류",
    "고객센터", "상담", "서비스", "보증", "수리", "전원", "연결",
]


def is_out_of_scope_query(user_message: str | None) -> bool:
    if not user_message:
        return False

    text = user_message.strip()

    has_out_scope = any(word in text for word in OUT_OF_SCOPE_KEYWORDS)
    has_domain = any(word in text for word in DOMAIN_KEYWORDS)

    return has_out_scope and not has_domain


def evaluate_docs(
    sources: list[dict] | None,
    user_message: str | None = None,
) -> str:
    """
    반환값:
    - good: 검색 결과가 충분함
    - bad: 결과는 있으나 품질이 낮음
    - no_docs: 검색 결과 없음 또는 상담 범위 밖 질문
    """
    if is_out_of_scope_query(user_message):
        return "no_docs"

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
        "삼성전자 제품 또는 서비스 관련 문의라면 아래 정보를 추가로 알려주세요.\n"
        "1. 제품 종류 또는 모델명\n"
        "2. 화면에 표시되는 에러 문구\n"
        "3. 발생 상황\n"
        "4. 이미 시도한 조치\n\n"
        f"질문 내용: {user_message}"
    )


def build_retry_query(user_message: str) -> str:
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