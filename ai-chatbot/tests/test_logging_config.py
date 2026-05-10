import logging
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.logging_config import _resolve_log_level


class LoggingConfigTest(unittest.TestCase):
    def test_resolve_log_level_accepts_known_level(self):
        self.assertEqual(_resolve_log_level("debug"), logging.DEBUG)

    def test_resolve_log_level_defaults_to_info_for_unknown_level(self):
        self.assertEqual(_resolve_log_level("not-a-level"), logging.INFO)


if __name__ == "__main__":
    unittest.main()
