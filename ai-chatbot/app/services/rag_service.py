import re

from app.core.settings import settings
from app.services.hybrid_retrieval_service import hybrid_search
from app.services.reranker_service import rerank_documents
from app.services.chat_history_service import (
    setup_chat_db,
    create_conversation,
    add_message,
    get_recent_messages
)
from app.services.document_registry_service import get_parsed_session_documents
from app.services.llm_routing_service import generate_with_routing, stream_with_routing
from app.services.llm_adapters.factory import get_llm_adapter


def _needs_korean_cleanup(text: str) -> bool:
    if not text:
        return False

    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", text):
        return True

    english_words = re.findall(r"\b[A-Za-z]{3,}\b", text)
    korean_chars = re.findall(r"[가-힣]", text)

    if english_words and len(english_words) >= 5 and len(korean_chars) < 80:
        return True

    return False


def _cleanup_to_korean(provider: str, answer: str) -> str:
    cleanup_system_prompt = """
당신은 한국어 문장 교정기입니다.

규칙:
1. 반드시 자연스러운 한국어로만 다시 작성하세요.
2. 영어, 일본어, 중국어, 태국어를 섞지 마세요.
3. 의미를 바꾸지 말고 표현만 한국어로 정리하세요.
4. 불필요하게 장황하게 쓰지 마세요.
""".strip()

    cleanup_user_prompt = f"""
다음 답변을 자연스러운 한국어만 사용해서 다시 작성하세요.

원문:
{answer}
""".strip()

    adapter = get_llm_adapter(provider)
    cleaned = adapter.generate(cleanup_system_prompt, cleanup_user_prompt).strip()
    return cleaned or answer


def _build_prompts(user_message: str, conversation_id: int):
    history = get_recent_messages(conversation_id, limit=6)

    session_docs = get_parsed_session_documents(conversation_id)
    kb_results = hybrid_search(
        user_message,
        limit=settings.TOP_K_RETRIEVAL
    )

    merged_candidates = []
    merged_candidates.extend(session_docs)
    merged_candidates.extend(kb_results)

    reranked = rerank_documents(
        query=user_message,
        documents=merged_candidates,
        top_n=settings.TOP_N_RERANK
    )

    context_blocks = []
    sources = []

    for item in reranked:
        context_blocks.append(
            f"[출처:{item['source']} / chunk:{item.get('chunk_index', 0)} / type:{item.get('search_type', 'kb')}]\n{item['content']}"
        )
        sources.append({
            "source": item["source"],
            "chunk_index": item.get("chunk_index", 0),
            "search_type": item.get("search_type", "kb"),
            "rerank_score": item.get("rerank_score")
        })

    context_text = "\n\n".join(context_blocks)

    history_text = ""
    for msg in history:
        prefix = "사용자" if msg["role"] == "user" else "AI"
        history_text += f"{prefix}: {msg['content']}\n"

    system_prompt = """
당신은 삼성전자 고객센터 AI 상담사입니다.

규칙:
1. 제공된 참고 문서 중심으로만 답변하세요.
2. 이전 대화 맥락이 있으면 자연스럽게 이어서 답하세요.
3. 문서에 없는 내용은 추측하지 마세요.
4. 간결하고 친절하게 답변하세요.
5. 반드시 한국어로만 답변하세요.
6. 영어, 일본어, 중국어, 태국어 등 다른 언어를 섞지 마세요.
7. 문서에 영어 용어가 있더라도 설명은 한국어로 작성하세요.
8. 답변은 먼저 핵심 해결 방법부터 말하고, 필요하면 추가 확인 사항을 덧붙이세요.
9. 사용자가 업로드한 세션 문서가 있으면 우선 참고하고, 부족하면 공식 KB를 참고하세요.
""".strip()

    user_prompt = f"""
이전 대화:
{history_text}

현재 질문:
{user_message}

참고 문서:
{context_text}
""".strip()

    return system_prompt, user_prompt, sources


def ask_rag(user_message: str, conversation_id: int | None = None) -> dict:
    setup_chat_db()

    if conversation_id is None:
        conversation_id = create_conversation()

    system_prompt, user_prompt, sources = _build_prompts(
        user_message=user_message,
        conversation_id=conversation_id
    )

    answer, used_provider = generate_with_routing(system_prompt, user_prompt)
    answer = answer.strip()

    if used_provider == "ollama" and _needs_korean_cleanup(answer):
        answer = _cleanup_to_korean(used_provider, answer)

    add_message(conversation_id, "user", user_message)
    add_message(conversation_id, "assistant", answer)

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources,
        "used_provider": used_provider
    }


def ask_rag_stream(user_message: str, conversation_id: int | None = None):
    setup_chat_db()

    if conversation_id is None:
        conversation_id = create_conversation()

    system_prompt, user_prompt, sources = _build_prompts(
        user_message=user_message,
        conversation_id=conversation_id
    )

    add_message(conversation_id, "user", user_message)

    chunks = []
    used_provider = None

    for token, provider in stream_with_routing(system_prompt, user_prompt):
        used_provider = provider
        chunks.append(token)
        yield {
            "type": "token",
            "conversation_id": conversation_id,
            "content": token,
            "used_provider": provider
        }

    answer = "".join(chunks).strip()

    if used_provider == "ollama" and _needs_korean_cleanup(answer):
        answer = _cleanup_to_korean(used_provider, answer)

    add_message(conversation_id, "assistant", answer)

    yield {
        "type": "done",
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources,
        "used_provider": used_provider
    }