import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import document_registry_service, file_storage_service
from app.services import managed_workflow_service
from app.services.managed_workflow_service import (
    delete_managed_document_if_allowed,
    force_delete_managed_document,
)


class ManagedWorkflowServiceTest(unittest.TestCase):
    def _create_test_db(self, db_path: Path, storage_path: Path, status: str = "draft"):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE managed_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT,
                original_name TEXT NOT NULL,
                saved_name TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                mime_type TEXT,
                file_extension TEXT,
                file_category TEXT,
                file_size INTEGER,
                parsed_text TEXT,
                version TEXT,
                status TEXT NOT NULL,
                approved_by TEXT,
                approved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                document_key TEXT,
                is_active INTEGER DEFAULT 0,
                parent_document_id INTEGER
            )
        """)
        cur.execute(
            """
            INSERT INTO managed_documents (
                title, category, original_name, saved_name, storage_path,
                status, created_at, updated_at, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "title",
                "category",
                "original.txt",
                storage_path.name,
                str(storage_path),
                status,
                "2026-05-06T00:00:00",
                "2026-05-06T00:00:00",
                1 if status == "indexed" else 0,
            ),
        )
        document_id = cur.lastrowid

        conn.commit()
        conn.close()

        return document_id

    def _insert_managed_document(
        self,
        db_path: Path,
        *,
        storage_path: Path,
        status: str,
        document_key: str,
        version: str,
        is_active: int,
    ) -> int:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO managed_documents (
                title, category, original_name, saved_name, storage_path,
                status, version, created_at, updated_at, document_key, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "title",
                "category",
                storage_path.name,
                storage_path.name,
                str(storage_path),
                status,
                version,
                "2026-05-06T00:00:00",
                "2026-05-06T00:00:00",
                document_key,
                is_active,
            ),
        )
        document_id = cur.lastrowid

        conn.commit()
        conn.close()

        return document_id

    def test_delete_managed_document_removes_row_and_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "app_state.db"
            upload_dir = Path(temp_dir) / "managed"
            upload_dir.mkdir()
            stored_file = upload_dir / "stored.txt"
            stored_file.write_text("hello", encoding="utf-8")
            document_id = self._create_test_db(db_path, stored_file)

            with patch.object(document_registry_service, "DB_PATH", db_path):
                with patch.object(file_storage_service.settings, "MANAGED_UPLOAD_DIR", str(upload_dir)):
                    result = delete_managed_document_if_allowed(document_id)
                    deleted_doc = document_registry_service.get_managed_document(document_id)

        self.assertTrue(result["deleted"])
        self.assertTrue(result["file_deleted"])
        self.assertIsNone(deleted_doc)
        self.assertFalse(stored_file.exists())

    def test_force_delete_managed_document_removes_indexed_document(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "app_state.db"
            upload_dir = Path(temp_dir) / "managed"
            upload_dir.mkdir()
            stored_file = upload_dir / "stored.txt"
            stored_file.write_text("hello", encoding="utf-8")
            document_id = self._create_test_db(db_path, stored_file, status="indexed")

            with patch.object(document_registry_service, "DB_PATH", db_path):
                with patch.object(file_storage_service.settings, "MANAGED_UPLOAD_DIR", str(upload_dir)):
                    with patch.object(
                        managed_workflow_service,
                        "delete_managed_document_vectors",
                        return_value=3,
                    ):
                        with patch.object(
                            managed_workflow_service,
                            "delete_managed_document_keyword_index",
                            return_value=3,
                        ):
                            result = force_delete_managed_document(document_id)
                            deleted_doc = document_registry_service.get_managed_document(document_id)

        self.assertEqual(result["previous_status"], "indexed")
        self.assertTrue(result["forced"])
        self.assertTrue(result["file_deleted"])
        self.assertEqual(result["vector_deleted"], 3)
        self.assertEqual(result["keyword_deleted"], 3)
        self.assertIsNone(deleted_doc)
        self.assertFalse(stored_file.exists())

    def test_force_delete_managed_document_skips_index_cleanup_for_draft_document(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "app_state.db"
            upload_dir = Path(temp_dir) / "managed"
            upload_dir.mkdir()
            stored_file = upload_dir / "stored.txt"
            stored_file.write_text("hello", encoding="utf-8")
            document_id = self._create_test_db(db_path, stored_file, status="draft")

            with patch.object(document_registry_service, "DB_PATH", db_path):
                with patch.object(file_storage_service.settings, "MANAGED_UPLOAD_DIR", str(upload_dir)):
                    with patch.object(
                        managed_workflow_service,
                        "delete_managed_document_vectors",
                    ) as delete_vectors:
                        with patch.object(
                            managed_workflow_service,
                            "delete_managed_document_keyword_index",
                        ) as delete_keyword:
                            result = force_delete_managed_document(document_id)

        delete_vectors.assert_not_called()
        delete_keyword.assert_not_called()
        self.assertEqual(result["previous_status"], "draft")
        self.assertEqual(result["vector_deleted"], 0)
        self.assertEqual(result["keyword_deleted"], 0)

    def test_force_delete_active_document_restores_latest_retired_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "app_state.db"
            upload_dir = Path(temp_dir) / "managed"
            upload_dir.mkdir()
            active_file = upload_dir / "active.txt"
            retired_file = upload_dir / "retired.txt"
            active_file.write_text("active", encoding="utf-8")
            retired_file.write_text("retired", encoding="utf-8")

            self._create_test_db(db_path, active_file, status="draft")

            conn = sqlite3.connect(db_path)
            conn.execute("DELETE FROM managed_documents")
            conn.commit()
            conn.close()

            retired_id = self._insert_managed_document(
                db_path,
                storage_path=retired_file,
                status="retired",
                document_key="title:category",
                version="v1",
                is_active=0,
            )
            active_id = self._insert_managed_document(
                db_path,
                storage_path=active_file,
                status="indexed",
                document_key="title:category",
                version="v2",
                is_active=1,
            )

            with patch.object(document_registry_service, "DB_PATH", db_path):
                with patch.object(file_storage_service.settings, "MANAGED_UPLOAD_DIR", str(upload_dir)):
                    with patch.object(
                        managed_workflow_service,
                        "delete_managed_document_vectors",
                        return_value=2,
                    ):
                        with patch.object(
                            managed_workflow_service,
                            "delete_managed_document_keyword_index",
                            return_value=2,
                        ):
                            result = force_delete_managed_document(active_id)
                            restored_doc = document_registry_service.get_managed_document(retired_id)
                            deleted_doc = document_registry_service.get_managed_document(active_id)
                            active_file_exists = active_file.exists()
                            retired_file_exists = retired_file.exists()

        self.assertTrue(result["forced"])
        self.assertEqual(result["restored_document_id"], retired_id)
        self.assertIsNone(deleted_doc)
        self.assertEqual(restored_doc["status"], "indexed")
        self.assertEqual(restored_doc["is_active"], 1)
        self.assertFalse(active_file_exists)
        self.assertTrue(retired_file_exists)


if __name__ == "__main__":
    unittest.main()
