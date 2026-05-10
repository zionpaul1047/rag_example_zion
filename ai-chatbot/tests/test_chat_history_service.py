import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import chat_history_service


class ChatHistoryServiceTest(unittest.TestCase):
    def test_setup_chat_db_adds_username_and_metadata_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat_history.db"

            with patch.object(chat_history_service, "DB_PATH", db_path):
                chat_history_service.setup_chat_db()

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(conversations)")
            conversation_columns = {row[1] for row in cur.fetchall()}
            cur.execute("PRAGMA table_info(messages)")
            message_columns = {row[1] for row in cur.fetchall()}
            conn.close()

        self.assertIn("username", conversation_columns)
        self.assertIn("metadata", message_columns)

    def test_create_conversation_stores_username(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "chat_history.db"

            with patch.object(chat_history_service, "DB_PATH", db_path):
                chat_history_service.setup_chat_db()
                conversation_id = chat_history_service.create_conversation("zion")

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT username FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            username = cur.fetchone()[0]
            conn.close()

        self.assertEqual(username, "zion")


if __name__ == "__main__":
    unittest.main()
