import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.rag_pipeline.langgraph_pipeline import (
    run_langgraph_rag_pipeline,
    run_langgraph_rag_stream_pipeline,
)


class FakeDeps:
    def __init__(
        self,
        *,
        prompt_scores: list[float | None] | None = None,
        prompt_metadata: dict | None = None,
        stream_error: Exception | None = None,
    ):
        self.prompt_scores = list(prompt_scores or [4.0])
        self.prompt_metadata = prompt_metadata
        self.stream_error = stream_error
        self.prompt_calls = []
        self.messages = []
        self.titles = []

    def setup_chat_db(self):
        pass

    def create_conversation(self):
        return 101

    def generate_title(self, user_message, llm_provider):
        return f"title:{user_message}:{llm_provider}"

    def update_conversation_title(self, conversation_id, title):
        self.titles.append((conversation_id, title))

    def build_prompts(self, query, conversation_id):
        self.prompt_calls.append((query, conversation_id))

        if not self.prompt_scores:
            score = 4.0
        else:
            score = self.prompt_scores.pop(0)

        sources = [] if score is None else [{"rerank_score": score}]
        if self.prompt_metadata is not None:
            return "system prompt", "user prompt", sources, self.prompt_metadata

        return "system prompt", "user prompt", sources

    def generate_answer(self, system_prompt, user_prompt, llm_provider):
        return "generated answer", "fake"

    def stream_answer(self, system_prompt, user_prompt, llm_provider):
        if self.stream_error:
            raise self.stream_error

        yield "streamed ", "fake"
        yield "answer", "fake"

    def needs_korean_cleanup(self, answer):
        return False

    def cleanup_to_korean(self, provider, answer):
        return answer

    def add_message(self, conversation_id, role, content, metadata=None):
        self.messages.append((conversation_id, role, content, metadata))


def make_state(**overrides):
    state = {
        "user_message": "question",
        "conversation_id": None,
        "llm_provider": "auto",
        "retry_count": 0,
    }
    state.update(overrides)
    return state


class LangGraphPipelineTest(unittest.TestCase):
    def test_run_pipeline_generates_and_saves_history(self):
        deps = FakeDeps(prompt_scores=[4.0])

        result = run_langgraph_rag_pipeline(make_state(), deps)

        self.assertEqual(result["conversation_id"], 101)
        self.assertEqual(result["answer"], "generated answer")
        self.assertEqual(result["used_provider"], "fake")
        self.assertEqual(result["graph_trace"], [
            "prepare",
            "retrieve",
            "generate",
            "save_history",
        ])
        self.assertEqual(deps.messages, [
            (101, "user", "question", None),
            (101, "assistant", "generated answer", {
                "sources": [{"rerank_score": 4.0}],
                "used_provider": "fake",
                "requested_provider": "auto",
                "eval_result": "good",
                "retry_count": 0,
                "graph": "langgraph",
                "graph_trace": [
                    "prepare",
                    "retrieve",
                    "generate",
                    "save_history",
                ],
                "error": None,
                "error_node": None,
            }),
        ])

    def test_run_pipeline_retries_bad_retrieval_once(self):
        deps = FakeDeps(prompt_scores=[1.0, 4.0])

        result = run_langgraph_rag_pipeline(make_state(), deps)

        self.assertEqual(result["retry_count"], 1)
        self.assertEqual(result["eval_result"], "good")
        self.assertEqual(len(deps.prompt_calls), 2)
        self.assertIn("retry_query", result["metadata"])
        self.assertEqual(result["graph_trace"], [
            "prepare",
            "retrieve",
            "retry_retrieve",
            "generate",
            "save_history",
        ])

    def test_run_pipeline_keeps_prompt_metadata(self):
        deps = FakeDeps(
            prompt_scores=[4.0],
            prompt_metadata={
                "retrieval_debug": {
                    "session_document_count": 1,
                    "kb_result_count": 2,
                    "source_count": 1,
                }
            },
        )

        result = run_langgraph_rag_pipeline(make_state(), deps)

        self.assertEqual(result["metadata"]["retrieval_debug"]["source_count"], 1)
        self.assertEqual(
            deps.messages[-1][3]["retrieval_debug"]["session_document_count"],
            1,
        )

    def test_run_pipeline_logs_rag_summary(self):
        deps = FakeDeps(
            prompt_scores=[4.0],
            prompt_metadata={
                "retrieval_debug": {
                    "session_document_count": 1,
                    "kb_result_count": 2,
                    "merged_candidate_count": 3,
                    "reranked_count": 1,
                    "filtered_reranked_count": 1,
                }
            },
        )

        with self.assertLogs(
            "app.services.rag_pipeline.langgraph_pipeline",
            level="INFO",
        ) as logs:
            run_langgraph_rag_pipeline(make_state(), deps)

        log_output = "\n".join(logs.output)
        self.assertIn("rag_summary conversation_id=101", log_output)
        self.assertIn("source_count=1", log_output)
        self.assertIn("session_document_count=1", log_output)
        self.assertIn("kb_result_count=2", log_output)
        self.assertIn("eval_result=good", log_output)

    def test_run_pipeline_returns_no_docs_answer_without_generation(self):
        deps = FakeDeps(prompt_scores=[None])

        result = run_langgraph_rag_pipeline(make_state(), deps)

        self.assertEqual(result["used_provider"], "system")
        self.assertEqual(result["eval_result"], "no_docs")
        self.assertIn("no_docs_answer", result["graph_trace"])
        self.assertEqual(len(deps.messages), 2)

    def test_stream_pipeline_emits_tokens_and_done_event(self):
        deps = FakeDeps(prompt_scores=[4.0])

        events = list(run_langgraph_rag_stream_pipeline(make_state(), deps))

        self.assertEqual([event["type"] for event in events], ["token", "token", "done"])
        self.assertEqual(events[-1]["answer"], "streamed answer")
        self.assertEqual(events[-1]["used_provider"], "fake")
        self.assertEqual(events[-1]["graph_trace"], [
            "prepare",
            "retrieve",
            "stream_generate",
            "save_history",
        ])
        self.assertEqual(deps.messages, [
            (101, "user", "question", None),
            (101, "assistant", "streamed answer", {
                "sources": [{"rerank_score": 4.0}],
                "used_provider": "fake",
                "requested_provider": "auto",
                "eval_result": "good",
                "retry_count": 0,
                "graph": "langgraph",
                "graph_trace": [
                    "prepare",
                    "retrieve",
                    "stream_generate",
                    "save_history",
                ],
                "error": None,
                "error_node": None,
            }),
        ])

    def test_stream_pipeline_retries_before_streaming(self):
        deps = FakeDeps(prompt_scores=[1.0, 4.0])

        events = list(run_langgraph_rag_stream_pipeline(make_state(), deps))

        self.assertEqual(events[-1]["retry_count"], 1)
        self.assertEqual(events[-1]["metadata"]["retry_query"], (
            "question 문제 해결 확인 설정 연결 전원 오류 에러"
        ))
        self.assertEqual(events[-1]["graph_trace"], [
            "prepare",
            "retrieve",
            "retry_retrieve",
            "stream_generate",
            "save_history",
        ])

    def test_stream_pipeline_keeps_prompt_metadata(self):
        deps = FakeDeps(
            prompt_scores=[4.0],
            prompt_metadata={
                "retrieval_debug": {
                    "session_document_count": 1,
                    "kb_result_count": 2,
                    "source_count": 1,
                }
            },
        )

        events = list(run_langgraph_rag_stream_pipeline(make_state(), deps))

        self.assertEqual(
            events[-1]["metadata"]["retrieval_debug"]["kb_result_count"],
            2,
        )
        self.assertEqual(deps.messages[-1][3]["retrieval_debug"]["source_count"], 1)

    def test_stream_pipeline_logs_rag_summary(self):
        deps = FakeDeps(
            prompt_scores=[4.0],
            prompt_metadata={
                "retrieval_debug": {
                    "session_document_count": 1,
                    "kb_result_count": 2,
                    "merged_candidate_count": 3,
                    "reranked_count": 1,
                    "filtered_reranked_count": 1,
                }
            },
        )

        with self.assertLogs(
            "app.services.rag_pipeline.langgraph_pipeline",
            level="INFO",
        ) as logs:
            list(run_langgraph_rag_stream_pipeline(make_state(), deps))

        log_output = "\n".join(logs.output)
        self.assertIn("rag_summary conversation_id=101", log_output)
        self.assertIn("source_count=1", log_output)
        self.assertIn("used_provider=fake", log_output)
        self.assertIn("graph_trace=prepare->retrieve->stream_generate->save_history", log_output)

    def test_stream_pipeline_returns_fallback_on_stream_error(self):
        deps = FakeDeps(prompt_scores=[4.0], stream_error=RuntimeError("boom"))

        events = list(run_langgraph_rag_stream_pipeline(make_state(), deps))

        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(events[-1]["used_provider"], "fallback")
        self.assertEqual(events[-1]["error"], "boom")
        self.assertEqual(events[-1]["error_node"], "stream_generate")
        self.assertIn("fallback_answer", events[-1]["graph_trace"])


if __name__ == "__main__":
    unittest.main()
