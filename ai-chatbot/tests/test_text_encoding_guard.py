import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


REPO_ROOT = Path(__file__).resolve().parents[2]

KEY_TEXT_FILES = [
    "ai-chatbot/app/services/rag_service.py",
    "ai-chatbot/app/services/rag_pipeline/langgraph_pipeline.py",
    "ai-chatbot/app/services/llm_routing_service.py",
    "ai-chatbot/app/api/auth.py",
    "ai-chatbot/app/api/conversation.py",
    "ai-chatbot/app/api/upload.py",
    "ai-chatbot-ui/src/pages/ChatPage.jsx",
    "ai-chatbot-ui/src/pages/RagDocumentsPage.jsx",
    "ai-chatbot-ui/src/pages/SessionFilesPage.jsx",
]

MOJIBAKE_MARKERS = [
    "�",
    "媛",
    "臾",
    "愿",
    "異",
    "吏",
    "踰",
    "蹂",
    "寃",
    "嫄",
    "珥",
    "遺덈",
    "ㅽ뙣",
    "ㅻ쪟",
]


class TextEncodingGuardTest(unittest.TestCase):
    def test_key_user_facing_files_do_not_contain_mojibake_markers(self):
        failures = []

        for relative_path in KEY_TEXT_FILES:
            path = REPO_ROOT / relative_path
            text = path.read_text(encoding="utf-8")

            for marker in MOJIBAKE_MARKERS:
                if marker in text:
                    failures.append(f"{relative_path}: {marker}")

        self.assertEqual(failures, [])

    def test_rag_prompt_labels_are_korean(self):
        text = (REPO_ROOT / "ai-chatbot/app/services/rag_service.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("[출처:", text)
        self.assertIn('"사용자"', text)
        self.assertIn(r"[가-힣]", text)


if __name__ == "__main__":
    unittest.main()
