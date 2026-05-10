import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import document_registry_service


class DocumentRegistryServiceTest(unittest.TestCase):
    def _insert_session_doc(
        self,
        db_path: Path,
        *,
        user_id: str | None,
        conversation_id: int,
        original_name: str,
        doc_status: str = "parsed",
        parsed_text: str | None = "parsed text",
    ) -> int:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO session_documents (
                user_id, conversation_id, original_name, saved_name,
                storage_path, mime_type, file_extension, file_category,
                file_size, parsed_text, doc_status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                conversation_id,
                original_name,
                f"{original_name}.stored",
                str(db_path.parent / f"{original_name}.stored"),
                "text/plain",
                ".txt",
                "text_like",
                10,
                parsed_text,
                doc_status,
                "2026-05-06T00:00:00",
            ),
        )
        document_id = cur.lastrowid
        conn.commit()
        conn.close()

        return document_id

    def test_session_document_queries_filter_by_user_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "app_state.db"

            with patch.object(document_registry_service, "DB_PATH", db_path):
                document_registry_service.setup_document_registry()
                zion_doc_id = self._insert_session_doc(
                    db_path,
                    user_id="zion",
                    conversation_id=7,
                    original_name="zion.txt",
                )
                self._insert_session_doc(
                    db_path,
                    user_id="admin",
                    conversation_id=7,
                    original_name="admin.txt",
                )

                zion_docs = document_registry_service.list_session_documents(
                    conversation_id=7,
                    user_id="zion",
                )
                zion_doc = document_registry_service.get_session_document(
                    zion_doc_id,
                    user_id="zion",
                )
                rejected_doc = document_registry_service.get_session_document(
                    zion_doc_id,
                    user_id="admin",
                )

        self.assertEqual([doc["original_name"] for doc in zion_docs], ["zion.txt"])
        self.assertEqual(zion_doc["original_name"], "zion.txt")
        self.assertIsNone(rejected_doc)

    def test_parsed_session_documents_filter_by_user_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "app_state.db"

            with patch.object(document_registry_service, "DB_PATH", db_path):
                document_registry_service.setup_document_registry()
                self._insert_session_doc(
                    db_path,
                    user_id="zion",
                    conversation_id=7,
                    original_name="zion.txt",
                    parsed_text="zion content",
                )
                self._insert_session_doc(
                    db_path,
                    user_id="admin",
                    conversation_id=7,
                    original_name="admin.txt",
                    parsed_text="admin content",
                )

                docs = document_registry_service.get_parsed_session_documents(
                    conversation_id=7,
                    user_id="zion",
                )

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["source"], "zion.txt")
        self.assertEqual(docs[0]["content"], "zion content")


if __name__ == "__main__":
    unittest.main()
