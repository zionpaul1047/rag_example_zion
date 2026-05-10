import sqlite3
import sys
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import conversation_service
from app.services import document_registry_service, file_storage_service


class ConversationServiceTest(unittest.TestCase):
    def _create_test_db(self, db_path: Path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                title TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cur.execute(
            "INSERT INTO conversations (created_at, title) VALUES (?, ?)",
            ("2026-05-06T00:00:00", "test conversation"),
        )
        conversation_id = cur.lastrowid

        cur.executemany(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                (conversation_id, "user", "question", "2026-05-06T00:00:01"),
                (conversation_id, "assistant", "answer", "2026-05-06T00:00:02"),
            ],
        )

        conn.commit()
        conn.close()

        return conversation_id

    def test_delete_conversation_removes_conversation_and_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat_history.db"
            conversation_id = self._create_test_db(db_path)

            with patch.object(conversation_service, "DB_PATH", db_path):
                result = conversation_service.delete_conversation(conversation_id)
                messages = conversation_service.get_conversation_messages(conversation_id)
                conversations = conversation_service.list_conversations()

        self.assertEqual(result, {
            "deleted": True,
            "conversation_id": conversation_id,
            "message_count": 2,
            "session_document_count": 0,
            "session_file_deleted_count": 0,
            "session_cleanup_errors": [],
        })
        self.assertEqual(messages, [])
        self.assertEqual(conversations, [])

    def test_delete_conversation_reports_missing_conversation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat_history.db"
            self._create_test_db(db_path)

            with patch.object(conversation_service, "DB_PATH", db_path):
                result = conversation_service.delete_conversation(999)

        self.assertEqual(result, {
            "deleted": False,
            "conversation_id": 999,
            "message_count": 0,
            "session_document_count": 0,
            "session_file_deleted_count": 0,
            "session_cleanup_errors": [],
        })

    def test_get_conversation_messages_includes_sources_from_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat_history.db"
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            metadata = {
                "sources": [
                    {
                        "source": "manual.pdf",
                        "chunk_index": 1,
                        "search_type": "kb",
                        "rerank_score": 4.2,
                    }
                ],
                "used_provider": "openai",
            }
            cur.execute(
                """
                INSERT INTO messages
                    (conversation_id, role, content, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    7,
                    "assistant",
                    "answer",
                    "2026-05-06T00:00:02",
                    json.dumps(metadata),
                ),
            )
            conn.commit()
            conn.close()

            with patch.object(conversation_service, "DB_PATH", db_path):
                messages = conversation_service.get_conversation_messages(7)

        self.assertEqual(messages[0]["sources"], metadata["sources"])
        self.assertEqual(messages[0]["metadata"]["used_provider"], "openai")

    def test_list_conversations_filters_by_username(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat_history.db"
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    title TEXT,
                    username TEXT
                )
            """)
            cur.executemany(
                "INSERT INTO conversations (created_at, title, username) VALUES (?, ?, ?)",
                [
                    ("2026-05-06T00:00:00", "zion conversation", "zion"),
                    ("2026-05-06T00:00:01", "admin conversation", "admin"),
                    ("2026-05-06T00:00:02", "legacy conversation", None),
                ],
            )
            conn.commit()
            conn.close()
            del cur
            del conn

            with patch.object(conversation_service, "DB_PATH", db_path):
                conversations = conversation_service.list_conversations("zion")

        self.assertEqual(
            [item["title"] for item in conversations],
            ["legacy conversation", "zion conversation"],
        )

    def test_get_conversation_messages_rejects_other_users_conversation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat_history.db"
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    title TEXT,
                    username TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute(
                "INSERT INTO conversations (created_at, title, username) VALUES (?, ?, ?)",
                ("2026-05-06T00:00:00", "admin conversation", "admin"),
            )
            conversation_id = cur.lastrowid
            cur.execute(
                """
                INSERT INTO messages (conversation_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, "assistant", "secret", "2026-05-06T00:00:01"),
            )
            conn.commit()
            conn.close()

            with patch.object(conversation_service, "DB_PATH", db_path):
                messages = conversation_service.get_conversation_messages(
                    conversation_id,
                    "zion",
                )

        self.assertEqual(messages, [])

    def test_conversation_belongs_to_user_rejects_other_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat_history.db"
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    title TEXT,
                    username TEXT
                )
            """)
            cur.execute(
                "INSERT INTO conversations (created_at, title, username) VALUES (?, ?, ?)",
                ("2026-05-06T00:00:00", "admin conversation", "admin"),
            )
            conversation_id = cur.lastrowid
            conn.commit()
            conn.close()

            with patch.object(conversation_service, "DB_PATH", db_path):
                self.assertTrue(
                    conversation_service.conversation_belongs_to_user(
                        conversation_id,
                        "admin",
                    )
                )
                self.assertFalse(
                    conversation_service.conversation_belongs_to_user(
                        conversation_id,
                        "zion",
                    )
                )

    def test_delete_conversation_removes_session_documents_and_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            chat_db_path = Path(temp_dir) / "chat_history.db"
            registry_db_path = Path(temp_dir) / "app_state.db"
            upload_dir = Path(temp_dir) / "session"
            upload_dir.mkdir()

            conversation_id = self._create_test_db(chat_db_path)
            stored_file = upload_dir / "stored.txt"
            stored_file.write_text("hello", encoding="utf-8")

            conn = sqlite3.connect(registry_db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE session_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    conversation_id INTEGER,
                    original_name TEXT NOT NULL,
                    saved_name TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    mime_type TEXT,
                    file_extension TEXT,
                    file_category TEXT,
                    file_size INTEGER,
                    ocr_text TEXT,
                    vision_summary TEXT,
                    parsed_text TEXT,
                    doc_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                )
            """)
            cur.execute(
                """
                INSERT INTO session_documents (
                    user_id, conversation_id, original_name, saved_name,
                    storage_path, doc_status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "zion",
                    conversation_id,
                    "original.txt",
                    stored_file.name,
                    str(stored_file),
                    "parsed",
                    "2026-05-06T00:00:00",
                ),
            )
            conn.commit()
            conn.close()

            with patch.object(conversation_service, "DB_PATH", chat_db_path):
                with patch.object(document_registry_service, "DB_PATH", registry_db_path):
                    with patch.object(
                        file_storage_service.settings,
                        "SESSION_UPLOAD_DIR",
                        str(upload_dir),
                    ):
                        result = conversation_service.delete_conversation(conversation_id)
                        remaining_docs = document_registry_service.list_session_documents(
                            conversation_id
                        )

        self.assertTrue(result["deleted"])
        self.assertEqual(result["session_document_count"], 1)
        self.assertEqual(result["session_file_deleted_count"], 1)
        self.assertEqual(result["session_cleanup_errors"], [])
        self.assertEqual(remaining_docs, [])
        self.assertFalse(stored_file.exists())


if __name__ == "__main__":
    unittest.main()
