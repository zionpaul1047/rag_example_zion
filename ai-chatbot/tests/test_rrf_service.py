import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.settings import settings
from app.services.rrf_service import reciprocal_rank_fusion


class ReciprocalRankFusionTest(unittest.TestCase):
    def test_merges_vector_and_keyword_results_by_source_and_chunk(self):
        vector_results = [
            {"source": "a", "chunk_index": 1, "content": "A"},
            {"source": "b", "chunk_index": 2, "content": "B"},
        ]
        keyword_results = [
            {"source": "a", "chunk_index": 1, "content": "A"},
            {"source": "c", "chunk_index": 3, "content": "C"},
        ]

        fused = reciprocal_rank_fusion(vector_results, keyword_results, limit=10)

        self.assertEqual([item["source"] for item in fused], ["a", "b", "c"])
        self.assertEqual(fused[0]["vector_rank"], 1)
        self.assertEqual(fused[0]["keyword_rank"], 1)
        self.assertIsNone(fused[1]["keyword_rank"])
        self.assertIsNone(fused[2]["vector_rank"])

    def test_respects_limit(self):
        vector_results = [
            {"source": "a", "chunk_index": 1, "content": "A"},
            {"source": "b", "chunk_index": 2, "content": "B"},
        ]

        fused = reciprocal_rank_fusion(vector_results, [], limit=1)

        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0]["source"], "a")

    def test_calculates_weighted_rrf_score(self):
        vector_results = [{"source": "a", "chunk_index": 1, "content": "A"}]
        keyword_results = [{"source": "a", "chunk_index": 1, "content": "A"}]

        fused = reciprocal_rank_fusion(vector_results, keyword_results, limit=10)

        expected_score = (
            settings.HYBRID_VECTOR_WEIGHT * (1 / (settings.RRF_K + 1))
            + settings.HYBRID_KEYWORD_WEIGHT * (1 / (settings.RRF_K + 1))
        )
        self.assertAlmostEqual(fused[0]["rrf_score"], expected_score)

    def test_raises_clear_error_for_missing_required_fields(self):
        with self.assertRaisesRegex(
            ValueError,
            "vector result is missing required field\\(s\\): content",
        ):
            reciprocal_rank_fusion(
                [{"source": "a", "chunk_index": 1}],
                [],
            )


if __name__ == "__main__":
    unittest.main()
