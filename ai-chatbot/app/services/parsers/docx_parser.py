from pathlib import Path
from docx import Document
from app.services.parsers.base_parser import BaseParser


class DocxParser(BaseParser):
    def parse(self, file_path: Path) -> dict:
        document = Document(file_path)
        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if text:
                paragraphs.append(text)

        content = "\n".join(paragraphs)

        return {
            "source": file_path.name,
            "content": content,
            "file_type": "docx"
        }