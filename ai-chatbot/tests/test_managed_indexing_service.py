import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import managed_indexing_service
from app.services.elasticsearch_index_service import INDEX_NAME


class FakeCursor:
    def __init__(self, rowcount: int = 0):
        self.rowcount = rowcount
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        self.executed.append((query, params))


class FakeConn:
    def __init__(self, cursor: FakeCursor):
        self.cursor_instance = cursor

    def cursor(self):
        return self.cursor_instance


class FakeElasticsearch:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def delete_by_query(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class ManagedIndexingServiceTest(unittest.TestCase):
    def test_managed_source_uses_stable_managed_prefix(self):
        self.assertEqual(
            managed_indexing_service.managed_source(7, "manual.pdf"),
            "[managed:7]manual.pdf",
        )

    def test_delete_existing_vector_chunks_deletes_by_source(self):
        cursor = FakeCursor(rowcount=3)
        conn = FakeConn(cursor)

        deleted = managed_indexing_service.delete_existing_vector_chunks(
            conn,
            "[managed:7]manual.pdf",
        )

        self.assertEqual(deleted, 3)
        self.assertEqual(cursor.executed[0][1], ("[managed:7]manual.pdf",))
        self.assertIn("DELETE FROM documents WHERE source = %s", cursor.executed[0][0])

    def test_delete_existing_keyword_chunks_deletes_by_source(self):
        es = FakeElasticsearch({"deleted": 2})

        deleted = managed_indexing_service.delete_existing_keyword_chunks(
            es,
            "[managed:7]manual.pdf",
        )

        self.assertEqual(deleted, 2)
        self.assertEqual(es.calls[0]["index"], INDEX_NAME)
        self.assertEqual(
            es.calls[0]["query"],
            {"term": {"source": "[managed:7]manual.pdf"}},
        )
        self.assertTrue(es.calls[0]["refresh"])


if __name__ == "__main__":
    unittest.main()
