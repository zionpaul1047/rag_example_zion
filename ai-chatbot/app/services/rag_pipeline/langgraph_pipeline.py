import logging

from langgraph.graph import StateGraph, END

from app.services.rag_pipeline.state import RagState
from app.services.rag_pipeline.evaluator import (
    evaluate_docs,
    build_no_docs_answer,
    build_retry_query,
)
from app.services.rag_pipeline.pipeline import unpack_prompt_result

logger = logging.getLogger(__name__)


def add_trace(state: RagState, node_name: str) -> list[str]:
    return [*state.get("graph_trace", []), node_name]


def log_rag_summary(
    *,
    conversation_id: int | None,
    source_count: int,
    used_provider: str | None,
    requested_provider: str | None,
    eval_result: str | None,
    retry_count: int,
    metadata: dict | None = None,
    graph_trace: list[str] | None = None,
    error: str | None = None,
    error_node: str | None = None,
) -> None:
    retrieval_debug = (metadata or {}).get("retrieval_debug") or {}

    logger.info(
        (
            "rag_summary conversation_id=%s source_count=%s "
            "session_document_count=%s kb_result_count=%s "
            "merged_candidate_count=%s reranked_count=%s "
            "filtered_reranked_count=%s eval_result=%s "
            "requested_provider=%s used_provider=%s retry_count=%s "
            "error_node=%s graph_trace=%s"
        ),
        conversation_id,
        source_count,
        retrieval_debug.get("session_document_count"),
        retrieval_debug.get("kb_result_count"),
        retrieval_debug.get("merged_candidate_count"),
        retrieval_debug.get("reranked_count"),
        retrieval_debug.get("filtered_reranked_count"),
        eval_result,
        requested_provider,
        used_provider,
        retry_count,
        error_node if error else None,
        "->".join(graph_trace or []),
    )


def build_fallback_answer(error_message: str | None = None) -> str:
    return (
        "답변을 생성하는 중 일시적인 오류가 발생했습니다.\n\n"
        "잠시 후 다시 질문해 주세요. 문제가 계속되면 관리자에게 문의해 주세요."
    )


def build_message_metadata(
    state: RagState,
    *,
    sources: list[dict] | None = None,
    used_provider: str | None = None,
    requested_provider: str | None = None,
    eval_result: str | None = None,
    retry_count: int | None = None,
    graph_trace: list[str] | None = None,
    error: str | None = None,
    error_node: str | None = None,
) -> dict:
    metadata = dict(state.get("metadata", {}))
    metadata.update({
        "sources": sources if sources is not None else state.get("sources", []),
        "used_provider": used_provider or state.get("used_provider"),
        "requested_provider": requested_provider
        or state.get("requested_provider")
        or state.get("llm_provider", "auto"),
        "eval_result": eval_result or state.get("eval_result"),
        "retry_count": retry_count
        if retry_count is not None
        else state.get("retry_count", 0),
        "graph": "langgraph",
        "graph_trace": graph_trace if graph_trace is not None else state.get("graph_trace", []),
        "error": error if error is not None else state.get("error"),
        "error_node": error_node if error_node is not None else state.get("error_node"),
    })
    return metadata


def prepare_state(state: RagState, deps) -> RagState:
    deps.setup_chat_db()

    user_message = state["user_message"]
    llm_provider = state.get("llm_provider") or "auto"

    if state.get("conversation_id") is None:
        conversation_id = deps.create_conversation()
        title = deps.generate_title(user_message, llm_provider)
        deps.update_conversation_title(conversation_id, title)

        return {
            **state,
            "conversation_id": conversation_id,
            "graph_trace": add_trace(state, "prepare"),
        }

    return {
        **state,
        "graph_trace": add_trace(state, "prepare"),
    }


def retrieve_state(state: RagState, deps) -> RagState:
    try:
        system_prompt, user_prompt, sources, prompt_metadata = unpack_prompt_result(
            deps.build_prompts(
                state["user_message"],
                state["conversation_id"],
            )
        )

        return {
            **state,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "sources": sources,
            "eval_result": evaluate_docs(sources, state["user_message"]),
            "metadata": {
                **state.get("metadata", {}),
                **prompt_metadata,
            },
            "graph_trace": add_trace(state, "retrieve"),
        }

    except Exception as e:
        return {
            **state,
            "sources": [],
            "eval_result": "no_docs",
            "error": str(e),
            "error_node": "retrieve",
            "graph_trace": add_trace(state, "retrieve_error"),
        }


def retry_retrieve_state(state: RagState, deps) -> RagState:
    retry_count = state.get("retry_count", 0)

    if retry_count >= 1:
        return {
            **state,
            "graph_trace": add_trace(state, "retry_retrieve_skipped"),
        }

    retry_query = build_retry_query(state["user_message"])

    try:
        system_prompt, user_prompt, sources, prompt_metadata = unpack_prompt_result(
            deps.build_prompts(
                retry_query,
                state["conversation_id"],
            )
        )

        return {
            **state,
            "retry_count": retry_count + 1,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "sources": sources,
            "eval_result": evaluate_docs(sources, state["user_message"]),
            "metadata": {
                **state.get("metadata", {}),
                **prompt_metadata,
                "retry_query": retry_query,
            },
            "graph_trace": add_trace(state, "retry_retrieve"),
        }

    except Exception as e:
        return {
            **state,
            "retry_count": retry_count + 1,
            "eval_result": "no_docs",
            "error": str(e),
            "error_node": "retry_retrieve",
            "metadata": {
                **state.get("metadata", {}),
                "retry_query": retry_query,
            },
            "graph_trace": add_trace(state, "retry_retrieve_error"),
        }


def no_docs_answer_state(state: RagState) -> RagState:
    return {
        **state,
        "answer": build_no_docs_answer(state["user_message"]),
        "used_provider": "system",
        "requested_provider": state.get("llm_provider") or "auto",
        "graph_trace": add_trace(state, "no_docs_answer"),
    }


def generate_state(state: RagState, deps) -> RagState:
    llm_provider = state.get("llm_provider") or "auto"

    try:
        answer, used_provider = deps.generate_answer(
            state["system_prompt"],
            state["user_prompt"],
            llm_provider,
        )

        answer = (answer or "").strip()

        if used_provider == "ollama" and deps.needs_korean_cleanup(answer):
            answer = deps.cleanup_to_korean(used_provider, answer)

        return {
            **state,
            "answer": answer,
            "used_provider": used_provider,
            "requested_provider": llm_provider,
            "graph_trace": add_trace(state, "generate"),
        }

    except Exception as e:
        return {
            **state,
            "answer": "",
            "used_provider": "fallback",
            "requested_provider": llm_provider,
            "error": str(e),
            "error_node": "generate",
            "graph_trace": add_trace(state, "generate_error"),
        }


def fallback_answer_state(state: RagState) -> RagState:
    return {
        **state,
        "answer": build_fallback_answer(state.get("error")),
        "used_provider": "fallback",
        "requested_provider": state.get("llm_provider") or "auto",
        "graph_trace": add_trace(state, "fallback_answer"),
    }


def save_history_state(state: RagState, deps) -> RagState:
    graph_trace = add_trace(state, "save_history")

    deps.add_message(
        state["conversation_id"],
        "user",
        state["user_message"],
    )

    deps.add_message(
        state["conversation_id"],
        "assistant",
        state.get("answer", ""),
        build_message_metadata(state, graph_trace=graph_trace),
    )

    return {
        **state,
        "graph_trace": graph_trace,
    }


def route_after_eval(state: RagState) -> str:
    eval_result = state.get("eval_result")

    if eval_result == "no_docs":
        return "no_docs"

    if eval_result == "bad" and state.get("retry_count", 0) < 1:
        return "retry"

    return "generate"


def route_after_eval_without_generate(state: RagState) -> str:
    if state.get("eval_result") == "bad" and state.get("retry_count", 0) < 1:
        return "retry"

    return "done"


def route_after_generate(state: RagState) -> str:
    if state.get("error_node") == "generate":
        return "fallback"

    return "save"


def create_rag_graph(deps):
    graph = StateGraph(RagState)

    graph.add_node("prepare", lambda state: prepare_state(state, deps))
    graph.add_node("retrieve", lambda state: retrieve_state(state, deps))
    graph.add_node("retry_retrieve", lambda state: retry_retrieve_state(state, deps))
    graph.add_node("no_docs_answer", no_docs_answer_state)
    graph.add_node("generate", lambda state: generate_state(state, deps))
    graph.add_node("fallback_answer", fallback_answer_state)
    graph.add_node("save_history", lambda state: save_history_state(state, deps))

    graph.set_entry_point("prepare")

    graph.add_edge("prepare", "retrieve")

    graph.add_conditional_edges(
        "retrieve",
        route_after_eval,
        {
            "no_docs": "no_docs_answer",
            "retry": "retry_retrieve",
            "generate": "generate",
        },
    )

    graph.add_conditional_edges(
        "retry_retrieve",
        route_after_eval,
        {
            "no_docs": "no_docs_answer",
            "retry": "generate",
            "generate": "generate",
        },
    )

    graph.add_conditional_edges(
        "generate",
        route_after_generate,
        {
            "fallback": "fallback_answer",
            "save": "save_history",
        },
    )

    graph.add_edge("fallback_answer", "save_history")
    graph.add_edge("no_docs_answer", "save_history")
    graph.add_edge("save_history", END)

    return graph.compile()


def create_rag_graph_without_generate(deps):
    graph = StateGraph(RagState)

    graph.add_node("prepare", lambda state: prepare_state(state, deps))
    graph.add_node("retrieve", lambda state: retrieve_state(state, deps))
    graph.add_node("retry_retrieve", lambda state: retry_retrieve_state(state, deps))

    graph.set_entry_point("prepare")

    graph.add_edge("prepare", "retrieve")

    graph.add_conditional_edges(
        "retrieve",
        route_after_eval_without_generate,
        {
            "retry": "retry_retrieve",
            "done": END,
        },
    )

    graph.add_edge("retry_retrieve", END)

    return graph.compile()


def run_langgraph_rag_pipeline(state: RagState, deps) -> dict:
    app = create_rag_graph(deps)
    final_state = app.invoke(state)
    metadata = final_state.get("metadata", {})
    graph_trace = final_state.get("graph_trace", [])
    sources = final_state.get("sources", [])
    requested_provider = (
        final_state.get("requested_provider")
        or final_state.get("llm_provider", "auto")
    )

    log_rag_summary(
        conversation_id=final_state["conversation_id"],
        source_count=len(sources),
        used_provider=final_state.get("used_provider"),
        requested_provider=requested_provider,
        eval_result=final_state.get("eval_result"),
        retry_count=final_state.get("retry_count", 0),
        metadata=metadata,
        graph_trace=graph_trace,
        error=final_state.get("error"),
        error_node=final_state.get("error_node"),
    )

    return {
        "conversation_id": final_state["conversation_id"],
        "answer": final_state.get("answer", ""),
        "sources": sources,
        "used_provider": final_state.get("used_provider"),
        "requested_provider": requested_provider,
        "eval_result": final_state.get("eval_result"),
        "retry_count": final_state.get("retry_count", 0),
        "metadata": metadata,
        "graph": "langgraph",
        "graph_trace": graph_trace,
        "error": final_state.get("error"),
        "error_node": final_state.get("error_node"),
    }


def run_langgraph_rag_stream_pipeline(state: RagState, deps):
    app = create_rag_graph_without_generate(deps)
    prepared_state = app.invoke(state)

    conversation_id = prepared_state["conversation_id"]
    user_message = prepared_state["user_message"]
    llm_provider = prepared_state.get("llm_provider") or "auto"
    eval_result = prepared_state.get("eval_result")

    deps.add_message(conversation_id, "user", user_message)

    if eval_result == "no_docs":
        answer = build_no_docs_answer(user_message)
        graph_trace = [
            *prepared_state.get("graph_trace", []),
            "no_docs_answer",
            "save_history",
        ]

        deps.add_message(
            conversation_id,
            "assistant",
            answer,
            build_message_metadata(
                prepared_state,
                used_provider="system",
                requested_provider=llm_provider,
                eval_result=eval_result,
                retry_count=prepared_state.get("retry_count", 0),
                graph_trace=graph_trace,
            ),
        )

        log_rag_summary(
            conversation_id=conversation_id,
            source_count=len(prepared_state.get("sources", [])),
            used_provider="system",
            requested_provider=llm_provider,
            eval_result=eval_result,
            retry_count=prepared_state.get("retry_count", 0),
            metadata=prepared_state.get("metadata", {}),
            graph_trace=graph_trace,
            error=prepared_state.get("error"),
            error_node=prepared_state.get("error_node"),
        )

        yield {
            "type": "done",
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": prepared_state.get("sources", []),
            "used_provider": "system",
            "requested_provider": llm_provider,
            "eval_result": eval_result,
            "retry_count": prepared_state.get("retry_count", 0),
            "metadata": prepared_state.get("metadata", {}),
            "graph": "langgraph",
            "graph_trace": graph_trace,
            "error": prepared_state.get("error"),
            "error_node": prepared_state.get("error_node"),
        }
        return

    chunks = []
    used_provider = None

    try:
        for token, provider in deps.stream_answer(
            prepared_state["system_prompt"],
            prepared_state["user_prompt"],
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
                "retry_count": prepared_state.get("retry_count", 0),
                "metadata": prepared_state.get("metadata", {}),
                "graph": "langgraph",
                "graph_trace": [
                    *prepared_state.get("graph_trace", []),
                    "stream_generate",
                ],
            }

        answer = "".join(chunks).strip()

        if used_provider == "ollama" and deps.needs_korean_cleanup(answer):
            answer = deps.cleanup_to_korean(used_provider, answer)

    except Exception as e:
        answer = build_fallback_answer(str(e))
        used_provider = "fallback"
        graph_trace = [
            *prepared_state.get("graph_trace", []),
            "stream_generate_error",
            "fallback_answer",
            "save_history",
        ]

        deps.add_message(
            conversation_id,
            "assistant",
            answer,
            build_message_metadata(
                prepared_state,
                used_provider=used_provider,
                requested_provider=llm_provider,
                eval_result=eval_result,
                retry_count=prepared_state.get("retry_count", 0),
                graph_trace=graph_trace,
                error=str(e),
                error_node="stream_generate",
            ),
        )

        log_rag_summary(
            conversation_id=conversation_id,
            source_count=len(prepared_state.get("sources", [])),
            used_provider=used_provider,
            requested_provider=llm_provider,
            eval_result=eval_result,
            retry_count=prepared_state.get("retry_count", 0),
            metadata=prepared_state.get("metadata", {}),
            graph_trace=graph_trace,
            error=str(e),
            error_node="stream_generate",
        )

        yield {
            "type": "done",
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": prepared_state.get("sources", []),
            "used_provider": used_provider,
            "requested_provider": llm_provider,
            "eval_result": eval_result,
            "retry_count": prepared_state.get("retry_count", 0),
            "metadata": prepared_state.get("metadata", {}),
            "graph": "langgraph",
            "graph_trace": graph_trace,
            "error": str(e),
            "error_node": "stream_generate",
        }
        return

    graph_trace = [
        *prepared_state.get("graph_trace", []),
        "stream_generate",
        "save_history",
    ]

    deps.add_message(
        conversation_id,
        "assistant",
        answer,
        build_message_metadata(
            prepared_state,
            used_provider=used_provider,
            requested_provider=llm_provider,
            eval_result=eval_result,
            retry_count=prepared_state.get("retry_count", 0),
            graph_trace=graph_trace,
            error=None,
            error_node=None,
        ),
    )

    log_rag_summary(
        conversation_id=conversation_id,
        source_count=len(prepared_state.get("sources", [])),
        used_provider=used_provider,
        requested_provider=llm_provider,
        eval_result=eval_result,
        retry_count=prepared_state.get("retry_count", 0),
        metadata=prepared_state.get("metadata", {}),
        graph_trace=graph_trace,
        error=None,
        error_node=None,
    )

    yield {
        "type": "done",
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": prepared_state.get("sources", []),
        "used_provider": used_provider,
        "requested_provider": llm_provider,
        "eval_result": eval_result,
        "retry_count": prepared_state.get("retry_count", 0),
        "metadata": prepared_state.get("metadata", {}),
        "graph": "langgraph",
        "graph_trace": graph_trace,
        "error": None,
        "error_node": None,
    }
