import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import settings as settings_module


class SettingsHelperTest(unittest.TestCase):
    def test_get_str_returns_default_when_env_is_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(settings_module._get_str("MISSING_VALUE", "default"), "default")

    def test_get_str_strips_env_value(self):
        with patch.dict(os.environ, {"SAMPLE_VALUE": "  hello  "}, clear=True):
            self.assertEqual(settings_module._get_str("SAMPLE_VALUE"), "hello")

    def test_get_int_returns_default_and_warns_for_invalid_value(self):
        stdout = io.StringIO()

        with patch.dict(os.environ, {"SAMPLE_INT": "abc"}, clear=True):
            with redirect_stdout(stdout):
                value = settings_module._get_int("SAMPLE_INT", 10)

        self.assertEqual(value, 10)
        self.assertIn("환경변수 SAMPLE_INT 값이 정수가 아닙니다", stdout.getvalue())

    def test_get_float_returns_default_and_warns_for_invalid_value(self):
        stdout = io.StringIO()

        with patch.dict(os.environ, {"SAMPLE_FLOAT": "abc"}, clear=True):
            with redirect_stdout(stdout):
                value = settings_module._get_float("SAMPLE_FLOAT", 0.5)

        self.assertEqual(value, 0.5)
        self.assertIn("환경변수 SAMPLE_FLOAT 값이 실수가 아닙니다", stdout.getvalue())

    def test_get_bool_accepts_common_truthy_values(self):
        for truthy_value in ("1", "true", "yes", "y", "on"):
            with self.subTest(truthy_value=truthy_value):
                with patch.dict(os.environ, {"SAMPLE_BOOL": truthy_value}, clear=True):
                    self.assertTrue(settings_module._get_bool("SAMPLE_BOOL", False))

    def test_get_bool_returns_false_for_unknown_values(self):
        with patch.dict(os.environ, {"SAMPLE_BOOL": "no"}, clear=True):
            self.assertFalse(settings_module._get_bool("SAMPLE_BOOL", True))


if __name__ == "__main__":
    unittest.main()
