import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import chat


class ChatApiTest(unittest.TestCase):
    def test_validate_conversation_access_allows_new_conversation_without_token(self):
        self.assertIsNone(chat._validate_conversation_access(None, None))

    def test_validate_conversation_access_requires_login_for_existing_conversation(self):
        with self.assertRaises(HTTPException) as context:
            chat._validate_conversation_access(7, None)

        self.assertEqual(context.exception.status_code, 401)

    def test_validate_conversation_access_rejects_other_users_conversation(self):
        with patch.object(chat, "conversation_belongs_to_user", return_value=False):
            with self.assertRaises(HTTPException) as context:
                chat._validate_conversation_access(7, "zion")

        self.assertEqual(context.exception.status_code, 404)

    def test_validate_conversation_access_accepts_owned_conversation(self):
        with patch.object(chat, "conversation_belongs_to_user", return_value=True):
            self.assertIsNone(chat._validate_conversation_access(7, "zion"))


if __name__ == "__main__":
    unittest.main()
