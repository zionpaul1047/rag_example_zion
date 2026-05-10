import re

from app.core.settings import settings
from app.services.hybrid_retrieval_service import hybrid_search
from app.services.reranker_service import rerank_documents
from app.services.title_service import generate_title
from app.services.chat_history_service import (
    setup_chat_db,
    create_conversation,
    add_message,
    get_recent_messages,
    update_conversation_title,
)
from app.services.document_registry_service import (
    get_parsed_session_documents,
    get_active_managed_document_sources,
)
from app.services.llm_routing_service import generate_with_routing, stream_with_routing
from app.services.llm_adapters.factory import get_llm_adapter
from app.services.rag_pipeline.pipeline import RagPipelineDeps
from app.services.rag_pipeline.langgraph_pipeline import (
    run_langgraph_rag_pipeline,
    run_langgraph_rag_stream_pipeline,
)
from app.services.rag_pipeline.prompts import (
    KOREAN_CLEANUP_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT,
    build_cleanup_user_prompt,
    build_rag_user_prompt,
)


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
    adapter = get_llm_adapter(provider)
    cleaned = adapter.generate(
        KOREAN_CLEANUP_SYSTEM_PROMPT,
        build_cleanup_user_prompt(answer),
    ).strip()
    return cleaned or answer


def _generate_answer(system_prompt: str, user_prompt: str, llm_provider: str):
    provider = (llm_provider or "auto").lower()

    if provider == "auto":
        return generate_with_routing(system_prompt, user_prompt)

    adapter = get_llm_adapter(provider)
    answer = adapter.generate(system_prompt, user_prompt)

    return answer, provider


def _stream_answer(system_prompt: str, user_prompt: str, llm_provider: str):
    provider = (llm_provider or "auto").lower()

    if provider == "auto":
        yield from stream_with_routing(system_prompt, user_prompt)
        return

    adapter = get_llm_adapter(provider)

    if hasattr(adapter, "stream"):
        for token in adapter.stream(system_prompt, user_prompt):
            yield token, provider
    else:
        answer = adapter.generate(system_prompt, user_prompt)
        yield answer, provider


def _filter_inactive_managed_documents(documents: list[dict]) -> list[dict]:
    active_sources = get_active_managed_document_sources()

    if not active_sources:
        return documents

    filtered = []

    for item in documents:
        source_name = str(item.get("source", ""))

        if source_name.startswith("[managed:") or source_name.startswith("[managed]"):
            if source_name in active_sources:
                filtered.append(item)
            continue

        filtered.append(item)

    return filtered


def _build_retrieval_debug(
    *,
    history: list[dict],
    session_docs: list[dict],
    kb_results: list[dict],
    merged_candidates: list[dict],
    reranked_count: int,
    filtered_reranked: list[dict],
    sources: list[dict],
) -> dict:
    return {
        "history_message_count": len(history),
        "session_document_count": len(session_docs),
        "kb_result_count": len(kb_results),
        "merged_candidate_count": len(merged_candidates),
        "top_k_retrieval": settings.TOP_K_RETRIEVAL,
        "top_n_rerank": settings.TOP_N_RERANK,
        "reranked_count": reranked_count,
        "filtered_reranked_count": len(filtered_reranked),
        "inactive_managed_filtered_count": reranked_count - len(filtered_reranked),
        "source_count": len(sources),
        "top_sources": sources[:5],
    }


def _build_content_preview(content: str, limit: int = 300) -> str:
    normalized = " ".join(str(content or "").split())

    if len(normalized) <= limit:
        return normalized

    return f"{normalized[:limit].rstrip()}..."


def _build_prompts(
    user_message: str,
    conversation_id: int,
    username: str | None = None,
):
    history = get_recent_messages(conversation_id, limit=6)

    session_docs = get_parsed_session_documents(conversation_id, user_id=username)

    kb_results = hybrid_search(
        user_message,
        limit=settings.TOP_K_RETRIEVAL,
    )

    merged_candidates = []
    merged_candidates.extend(session_docs)
    merged_candidates.extend(kb_results)

    reranked = rerank_documents(
        query=user_message,
        documents=merged_candidates,
        top_n=settings.TOP_N_RERANK,
    )

    reranked_count = len(reranked)
    reranked = _filter_inactive_managed_documents(reranked)

    context_blocks = []
    sources = []

    for item in reranked:
        content = item["content"]
        context_blocks.append(
            (
                f"[출처:{item['source']} / "
                f"chunk:{item.get('chunk_index', 0)} / "
                f"type:{item.get('search_type', 'kb')}]\n"
                f"{content}"
            )
        )

        sources.append(
            {
                "source": item["source"],
                "chunk_index": item.get("chunk_index", 0),
                "search_type": item.get("search_type", "kb"),
                "rerank_score": item.get("rerank_score"),
                "content_preview": _build_content_preview(content),
            }
        )

    context_text = "\n\n".join(context_blocks)

    history_text = ""
    for msg in history:
        prefix = "사용자" if msg["role"] == "user" else "AI"
        history_text += f"{prefix}: {msg['content']}\n"

    user_prompt = build_rag_user_prompt(
        history_text=history_text,
        user_message=user_message,
        context_text=context_text,
    )

    retrieval_debug = _build_retrieval_debug(
        history=history,
        session_docs=session_docs,
        kb_results=kb_results,
        merged_candidates=merged_candidates,
        reranked_count=reranked_count,
        filtered_reranked=reranked,
        sources=sources,
    )

    return RAG_SYSTEM_PROMPT, user_prompt, sources, {
        "retrieval_debug": retrieval_debug,
    }


def ask_rag(
    user_message: str,
    conversation_id: int | None = None,
    llm_provider: str | None = "auto",
    username: str | None = None,
) -> dict:
    deps = RagPipelineDeps(
        setup_chat_db=setup_chat_db,
        create_conversation=lambda: create_conversation(username),
        add_message=add_message,
        update_conversation_title=update_conversation_title,
        generate_title=generate_title,
        build_prompts=lambda message, conversation_id: _build_prompts(
            message,
            conversation_id,
            username=username,
        ),
        generate_answer=_generate_answer,
        stream_answer=_stream_answer,
        needs_korean_cleanup=_needs_korean_cleanup,
        cleanup_to_korean=_cleanup_to_korean,
    )

    state = {
        "user_message": user_message,
        "conversation_id": conversation_id,
        "llm_provider": llm_provider or "auto",
        "retry_count": 0,
    }

    return run_langgraph_rag_pipeline(state, deps)


def ask_rag_stream(
    user_message: str,
    conversation_id: int | None = None,
    llm_provider: str | None = "auto",
    username: str | None = None,
):
    deps = RagPipelineDeps(
        setup_chat_db=setup_chat_db,
        create_conversation=lambda: create_conversation(username),
        add_message=add_message,
        update_conversation_title=update_conversation_title,
        generate_title=generate_title,
        build_prompts=lambda message, conversation_id: _build_prompts(
            message,
            conversation_id,
            username=username,
        ),
        generate_answer=_generate_answer,
        stream_answer=_stream_answer,
        needs_korean_cleanup=_needs_korean_cleanup,
        cleanup_to_korean=_cleanup_to_korean,
    )

    state = {
        "user_message": user_message,
        "conversation_id": conversation_id,
        "llm_provider": llm_provider or "auto",
        "retry_count": 0,
    }

    yield from run_langgraph_rag_stream_pipeline(state, deps)
