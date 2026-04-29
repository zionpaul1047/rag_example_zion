from langgraph.graph import StateGraph, END

from app.services.rag_pipeline.state import RagState
from app.services.rag_pipeline.evaluator import (
    evaluate_docs,
    build_no_docs_answer,
    build_retry_query,
)


def add_trace(state: RagState, node_name: str) -> list[str]:
    return [*state.get("graph_trace", []), node_name]


def build_fallback_answer(error_message: str | None = None) -> str:
    return (
        "답변을 생성하는 중 일시적인 오류가 발생했습니다.\n\n"
        "잠시 후 다시 질문해 주세요. 문제가 계속되면 관리자에게 문의해 주세요."
    )


def create_rag_graph(deps):
    graph = StateGraph(RagState)

    def prepare(state: RagState):
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

    def retrieve(state: RagState):
        try:
            system_prompt, user_prompt, sources = deps.build_prompts(
                state["user_message"],
                state["conversation_id"],
            )

            return {
                **state,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "sources": sources,
                "eval_result": evaluate_docs(sources, state["user_message"]),
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

    def retry_retrieve(state: RagState):
        retry_count = state.get("retry_count", 0)

        if retry_count >= 1:
            return {
                **state,
                "graph_trace": add_trace(state, "retry_retrieve_skipped"),
            }

        retry_query = build_retry_query(state["user_message"])

        try:
            system_prompt, user_prompt, sources = deps.build_prompts(
                retry_query,
                state["conversation_id"],
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

    def no_docs_answer(state: RagState):
        return {
            **state,
            "answer": build_no_docs_answer(state["user_message"]),
            "used_provider": "system",
            "requested_provider": state.get("llm_provider") or "auto",
            "graph_trace": add_trace(state, "no_docs_answer"),
        }

    def generate(state: RagState):
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

    def fallback_answer(state: RagState):
        return {
            **state,
            "answer": build_fallback_answer(state.get("error")),
            "used_provider": "fallback",
            "requested_provider": state.get("llm_provider") or "auto",
            "graph_trace": add_trace(state, "fallback_answer"),
        }

    def save_history(state: RagState):
        deps.add_message(
            state["conversation_id"],
            "user",
            state["user_message"],
        )

        deps.add_message(
            state["conversation_id"],
            "assistant",
            state.get("answer", ""),
        )

        return {
            **state,
            "graph_trace": add_trace(state, "save_history"),
        }

    def route_after_eval(state: RagState):
        eval_result = state.get("eval_result")

        if eval_result == "no_docs":
            return "no_docs"

        if eval_result == "bad" and state.get("retry_count", 0) < 1:
            return "retry"

        return "generate"

    def route_after_generate(state: RagState):
        if state.get("error_node") == "generate":
            return "fallback"

        return "save"

    graph.add_node("prepare", prepare)
    graph.add_node("retrieve", retrieve)
    graph.add_node("retry_retrieve", retry_retrieve)
    graph.add_node("no_docs_answer", no_docs_answer)
    graph.add_node("generate", generate)
    graph.add_node("fallback_answer", fallback_answer)
    graph.add_node("save_history", save_history)

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

    def prepare(state: RagState):
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

    def retrieve(state: RagState):
        try:
            system_prompt, user_prompt, sources = deps.build_prompts(
                state["user_message"],
                state["conversation_id"],
            )

            return {
                **state,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "sources": sources,
                "eval_result": evaluate_docs(sources, state["user_message"]),
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

    def retry_retrieve(state: RagState):
        retry_count = state.get("retry_count", 0)

        if retry_count >= 1:
            return {
                **state,
                "graph_trace": add_trace(state, "retry_retrieve_skipped"),
            }

        retry_query = build_retry_query(state["user_message"])

        try:
            system_prompt, user_prompt, sources = deps.build_prompts(
                retry_query,
                state["conversation_id"],
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

    def route_after_eval(state: RagState):
        eval_result = state.get("eval_result")

        if eval_result == "bad" and state.get("retry_count", 0) < 1:
            return "retry"

        return "done"

    graph.add_node("prepare", prepare)
    graph.add_node("retrieve", retrieve)
    graph.add_node("retry_retrieve", retry_retrieve)

    graph.set_entry_point("prepare")

    graph.add_edge("prepare", "retrieve")

    graph.add_conditional_edges(
        "retrieve",
        route_after_eval,
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

    return {
        "conversation_id": final_state["conversation_id"],
        "answer": final_state.get("answer", ""),
        "sources": final_state.get("sources", []),
        "used_provider": final_state.get("used_provider"),
        "requested_provider": final_state.get("requested_provider")
        or final_state.get("llm_provider", "auto"),
        "eval_result": final_state.get("eval_result"),
        "retry_count": final_state.get("retry_count", 0),
        "metadata": final_state.get("metadata", {}),
        "graph": "langgraph",
        "graph_trace": final_state.get("graph_trace", []),
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

        deps.add_message(conversation_id, "assistant", answer)

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
            "graph_trace": [
                *prepared_state.get("graph_trace", []),
                "no_docs_answer",
                "save_history",
            ],
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

        deps.add_message(conversation_id, "assistant", answer)

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
            "graph_trace": [
                *prepared_state.get("graph_trace", []),
                "stream_generate_error",
                "fallback_answer",
                "save_history",
            ],
            "error": str(e),
            "error_node": "stream_generate",
        }
        return

    deps.add_message(conversation_id, "assistant", answer)

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
        "graph_trace": [
            *prepared_state.get("graph_trace", []),
            "stream_generate",
            "save_history",
        ],
        "error": None,
        "error_node": None,
    }