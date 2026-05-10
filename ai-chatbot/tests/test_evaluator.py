import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.rag_pipeline.evaluator import (
    evaluate_docs,
    get_rerank_scores,
    has_relevant_rerank_score,
    is_out_of_scope_query,
)


class EvaluatorTest(unittest.TestCase):
    def test_evaluate_docs_returns_no_docs_for_empty_sources(self):
        self.assertEqual(evaluate_docs(None, "TV 화면 오류"), "no_docs")
        self.assertEqual(evaluate_docs([], "TV 화면 오류"), "no_docs")

    def test_evaluate_docs_returns_bad_for_low_rerank_score(self):
        sources = [{"rerank_score": 2.9}]

        self.assertEqual(evaluate_docs(sources, "TV 화면 오류"), "bad")

    def test_evaluate_docs_returns_good_for_relevant_rerank_score(self):
        sources = [{"rerank_score": 3.0}]

        self.assertEqual(evaluate_docs(sources, "TV 화면 오류"), "good")

    def test_evaluate_docs_returns_good_when_scores_are_missing(self):
        self.assertEqual(evaluate_docs([{}], "TV 화면 오류"), "good")

    def test_out_of_scope_query_requires_no_domain_keyword(self):
        self.assertTrue(is_out_of_scope_query("주식 추천해줘"))
        self.assertFalse(is_out_of_scope_query("TV 화면 오류"))
        self.assertFalse(is_out_of_scope_query("TV 보증 관련 법률 문의"))

    def test_get_rerank_scores_ignores_non_numeric_values(self):
        sources = [
            {"rerank_score": 1},
            {"rerank_score": 2.5},
            {"rerank_score": "3"},
            {},
        ]

        self.assertEqual(get_rerank_scores(sources), [1.0, 2.5])

    def test_has_relevant_rerank_score_treats_missing_scores_as_relevant(self):
        self.assertTrue(has_relevant_rerank_score([{}]))
        self.assertFalse(has_relevant_rerank_score([{"rerank_score": 2.9}]))
        self.assertTrue(has_relevant_rerank_score([{"rerank_score": 3.0}]))


if __name__ == "__main__":
    unittest.main()
