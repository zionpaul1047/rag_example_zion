import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import dependencies


class ApiDependenciesTest(unittest.TestCase):
    def test_require_authenticated_user_rejects_missing_token(self):
        with self.assertRaises(HTTPException) as context:
            dependencies.require_authenticated_user(None)

        self.assertEqual(context.exception.status_code, 401)

    def test_require_authenticated_user_accepts_any_valid_user(self):
        user = {
            "username": "zion",
            "role": "user",
            "display_name": "zion",
        }

        with patch.object(dependencies, "get_user_from_token", return_value=user):
            result = dependencies.require_authenticated_user("Bearer user-token")

        self.assertEqual(result, user)

    def test_require_admin_user_rejects_missing_token(self):
        with self.assertRaises(HTTPException) as context:
            dependencies.require_admin_user(None)

        self.assertEqual(context.exception.status_code, 401)

    def test_require_admin_user_rejects_non_admin_user(self):
        with patch.object(
            dependencies,
            "get_user_from_token",
            return_value={
                "username": "zion",
                "role": "user",
                "display_name": "zion",
            },
        ):
            with self.assertRaises(HTTPException) as context:
                dependencies.require_admin_user("Bearer user-token")

        self.assertEqual(context.exception.status_code, 403)

    def test_require_admin_user_accepts_admin_user(self):
        admin_user = {
            "username": "admin",
            "role": "admin",
            "display_name": "admin",
        }

        with patch.object(dependencies, "get_user_from_token", return_value=admin_user):
            result = dependencies.require_admin_user("Bearer admin-token")

        self.assertEqual(result, admin_user)


if __name__ == "__main__":
    unittest.main()
