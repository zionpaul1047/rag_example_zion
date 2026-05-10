import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import rag_service


class RagServicePromptTest(unittest.TestCase):
    def test_build_prompts_returns_retrieval_debug_metadata(self):
        history = [{"role": "user", "content": "old question"}]
        session_docs = [
            {
                "source": "session.pdf",
                "content": "session content",
                "chunk_index": 0,
                "search_type": "session",
            }
        ]
        kb_results = [
            {
                "source": "kb.md",
                "content": "kb content",
                "chunk_index": 1,
                "search_type": "vector",
            },
            {
                "source": "keyword.md",
                "content": "keyword content",
                "chunk_index": 2,
                "search_type": "keyword",
            },
        ]
        reranked = [
            {
                "source": "session.pdf",
                "content": "session content",
                "chunk_index": 0,
                "search_type": "session",
                "rerank_score": 5.0,
            },
            {
                "source": "kb.md",
                "content": "kb content",
                "chunk_index": 1,
                "search_type": "vector",
                "rerank_score": 4.0,
            },
        ]

        with (
            patch.object(rag_service, "get_recent_messages", return_value=history),
            patch.object(
                rag_service,
                "get_parsed_session_documents",
                return_value=session_docs,
            ),
            patch.object(rag_service, "hybrid_search", return_value=kb_results),
            patch.object(rag_service, "rerank_documents", return_value=reranked),
            patch.object(
                rag_service,
                "get_active_managed_document_sources",
                return_value=[],
            ),
        ):
            _, _, sources, metadata = rag_service._build_prompts(
                "question",
                conversation_id=7,
                username="zion",
            )

        debug = metadata["retrieval_debug"]

        self.assertEqual(debug["history_message_count"], 1)
        self.assertEqual(debug["session_document_count"], 1)
        self.assertEqual(debug["kb_result_count"], 2)
        self.assertEqual(debug["merged_candidate_count"], 3)
        self.assertEqual(debug["reranked_count"], 2)
        self.assertEqual(debug["filtered_reranked_count"], 2)
        self.assertEqual(debug["source_count"], 2)
        self.assertEqual(debug["top_sources"], sources[:5])
        self.assertEqual(sources[0]["content_preview"], "session content")


if __name__ == "__main__":
    unittest.main()
