from dataclasses import dataclass
from typing import Callable, Iterable

from app.services.rag_pipeline.query_rewriter import rewrite_query
from app.services.rag_pipeline.state import RagState
from app.services.rag_pipeline.evaluator import (
    evaluate_docs,
    build_no_docs_answer,
    build_retry_query,
)


@dataclass
class RagPipelineDeps:
    setup_chat_db: Callable[[], None]
    create_conversation: Callable[[], int]
    add_message: Callable[[int, str, str], None]
    update_conversation_title: Callable[[int, str], None]

    generate_title: Callable[[str, str], str]
    build_prompts: Callable[[str, int], tuple[str, str, list[dict]]]

    generate_answer: Callable[[str, str, str], tuple[str, str]]
    stream_answer: Callable[[str, str, str], Iterable[tuple[str, str]]]

    needs_korean_cleanup: Callable[[str], bool]
    cleanup_to_korean: Callable[[str, str], str]


def _prepare_conversation(state: RagState, deps: RagPipelineDeps) -> tuple[int, bool]:
    deps.setup_chat_db()

    user_message = state["user_message"]
    llm_provider = state.get("llm_provider") or "auto"

    is_new_conversation = state.get("conversation_id") is None

    if is_new_conversation:
        state["conversation_id"] = deps.create_conversation()

    conversation_id = state["conversation_id"]

    if is_new_conversation:
        title = deps.generate_title(user_message, llm_provider)
        deps.update_conversation_title(conversation_id, title)

    return conversation_id, is_new_conversation


def _build_and_evaluate(
    state: RagState,
    deps: RagPipelineDeps,
    query_message: str,
    conversation_id: int,
):
    system_prompt, user_prompt, sources = deps.build_prompts(
        query_message,
        conversation_id,
    )

    eval_result = evaluate_docs(sources, state["user_message"])

    state["system_prompt"] = system_prompt
    state["user_prompt"] = user_prompt
    state["sources"] = sources
    state["eval_result"] = eval_result

    return system_prompt, user_prompt, sources, eval_result


def _maybe_retry_retrieve(
    state: RagState,
    deps: RagPipelineDeps,
    conversation_id: int,
):
    user_message = state["user_message"]
    retry_count = state.get("retry_count", 0)

    if state.get("eval_result") != "bad":
        return

    if retry_count >= 1:
        return

    retry_query = build_retry_query(user_message)

    state["retry_count"] = retry_count + 1
    state["metadata"] = {
        **state.get("metadata", {}),
        "retry_query": retry_query,
    }

    system_prompt, user_prompt, sources = deps.build_prompts(
        retry_query,
        conversation_id,
    )

    eval_result = evaluate_docs(sources, state["user_message"])

    state["system_prompt"] = system_prompt
    state["user_prompt"] = user_prompt
    state["sources"] = sources
    state["eval_result"] = eval_result


def run_rag_pipeline(state: RagState, deps: RagPipelineDeps) -> dict:
    conversation_id, _ = _prepare_conversation(state, deps)

    user_message = state["user_message"]
    llm_provider = state.get("llm_provider") or "auto"

    rewritten_query = rewrite_query(
        user_message=user_message,
        conversation_id=conversation_id,
        provider=llm_provider,
    )

    state["original_query"] = user_message
    state["rewritten_query"] = rewritten_query
    state["metadata"] = {
        **state.get("metadata", {}),
        "original_query": user_message,
        "rewritten_query": rewritten_query,
    }

    _build_and_evaluate(
        state=state,
        deps=deps,
        query_message=rewritten_query,
        conversation_id=conversation_id,
    )

    _maybe_retry_retrieve(
        state=state,
        deps=deps,
        conversation_id=conversation_id,
    )

    eval_result = state.get("eval_result")

    if eval_result == "no_docs":
        answer = build_no_docs_answer(user_message)
        used_provider = "system"
    else:
        answer, used_provider = deps.generate_answer(
            state["system_prompt"],
            state["user_prompt"],
            llm_provider,
        )

        answer = (answer or "").strip()

        if used_provider == "ollama" and deps.needs_korean_cleanup(answer):
            answer = deps.cleanup_to_korean(used_provider, answer)

    state["answer"] = answer
    state["used_provider"] = used_provider
    state["requested_provider"] = llm_provider

    deps.add_message(conversation_id, "user", user_message)
    deps.add_message(conversation_id, "assistant", answer)

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": state.get("sources", []),
        "used_provider": used_provider,
        "requested_provider": llm_provider,
        "eval_result": eval_result,
        "retry_count": state.get("retry_count", 0),
        "metadata": state.get("metadata", {}),
    }


def stream_rag_pipeline(state: RagState, deps: RagPipelineDeps):
    conversation_id, _ = _prepare_conversation(state, deps)

    user_message = state["user_message"]
    llm_provider = state.get("llm_provider") or "auto"

    rewritten_query = rewrite_query(
        user_message=user_message,
        conversation_id=conversation_id,
        provider=llm_provider,
    )

    state["original_query"] = user_message
    state["rewritten_query"] = rewritten_query
    state["metadata"] = {
        **state.get("metadata", {}),
        "original_query": user_message,
        "rewritten_query": rewritten_query,
    }

    _build_and_evaluate(
        state=state,
        deps=deps,
        query_message=rewritten_query,
        conversation_id=conversation_id,
    )

    _maybe_retry_retrieve(
        state=state,
        deps=deps,
        conversation_id=conversation_id,
    )

    eval_result = state.get("eval_result")

    deps.add_message(conversation_id, "user", user_message)

    if eval_result == "no_docs":
        answer = build_no_docs_answer(user_message)

        deps.add_message(conversation_id, "assistant", answer)

        yield {
            "type": "done",
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": [],
            "used_provider": "system",
            "requested_provider": llm_provider,
            "eval_result": eval_result,
            "retry_count": state.get("retry_count", 0),
            "metadata": state.get("metadata", {}),
        }
        return

    chunks = []
    used_provider = None

    for token, provider in deps.stream_answer(
        state["system_prompt"],
        state["user_prompt"],
        llm_provider,
    ):
        used_provider = provider
        chunks.append(token)

        yield {
            "type": "token",
            "conversation_id": conversation_id,
            "content": token,
            "used_provider": provider,
            "requested_provider": llm_provider,
            "eval_result": eval_result,
            "retry_count": state.get("retry_count", 0),
            "metadata": state.get("metadata", {}),
        }

    answer = "".join(chunks).strip()

    if used_provider == "ollama" and deps.needs_korean_cleanup(answer):
        answer = deps.cleanup_to_korean(used_provider, answer)

    deps.add_message(conversation_id, "assistant", answer)

    yield {
        "type": "done",
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": state.get("sources", []),
        "used_provider": used_provider,
        "requested_provider": llm_provider,
        "eval_result": eval_result,
        "retry_count": state.get("retry_count", 0),
        "metadata": state.get("metadata", {}),
    }