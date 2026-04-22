from pathlib import Path
from pypdf import PdfReader
from app.services.parsers.base_parser import BaseParser


class PdfParser(BaseParser):
    def parse(self, file_path: Path) -> dict:
        reader = PdfReader(str(file_path))
        pages = []

        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())

        content = "\n\n".join(pages)

        return {
            "source": file_path.name,
            "content": content,
            "file_type": "pdf"
        }