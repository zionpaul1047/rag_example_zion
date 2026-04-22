from pathlib import Path
from app.services.parsers.base_parser import BaseParser


class MarkdownParser(BaseParser):
    def parse(self, file_path: Path) -> dict:
        content = file_path.read_text(encoding="utf-8")

        return {
            "source": file_path.name,
            "content": content,
            "file_type": "md"
        }