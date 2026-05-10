import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import file_storage_service


class FileStorageServiceTest(unittest.TestCase):
    def test_delete_stored_file_removes_file_inside_upload_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir) / "session"
            upload_dir.mkdir()
            target = upload_dir / "sample.txt"
            target.write_text("hello", encoding="utf-8")

            with patch.object(file_storage_service.settings, "SESSION_UPLOAD_DIR", str(upload_dir)):
                deleted = file_storage_service.delete_stored_file(str(target), scope="session")

            self.assertTrue(deleted)
            self.assertFalse(target.exists())

    def test_delete_stored_file_returns_false_when_file_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir) / "session"
            upload_dir.mkdir()
            target = upload_dir / "missing.txt"

            with patch.object(file_storage_service.settings, "SESSION_UPLOAD_DIR", str(upload_dir)):
                deleted = file_storage_service.delete_stored_file(str(target), scope="session")

            self.assertFalse(deleted)

    def test_delete_stored_file_rejects_paths_outside_upload_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir) / "session"
            outside_dir = Path(temp_dir) / "outside"
            upload_dir.mkdir()
            outside_dir.mkdir()
            target = outside_dir / "sample.txt"
            target.write_text("hello", encoding="utf-8")

            with patch.object(file_storage_service.settings, "SESSION_UPLOAD_DIR", str(upload_dir)):
                with self.assertRaisesRegex(ValueError, "업로드 디렉터리 밖의 파일"):
                    file_storage_service.delete_stored_file(str(target), scope="session")


if __name__ == "__main__":
    unittest.main()
