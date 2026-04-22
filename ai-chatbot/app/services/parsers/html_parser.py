from pathlib import Path
from bs4 import BeautifulSoup
from app.services.parsers.base_parser import BaseParser


class HtmlParser(BaseParser):
    def parse(self, file_path: Path) -> dict:
        html = file_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(cleaned_lines)

        return {
            "source": file_path.name,
            "content": content,
            "file_type": "html"
        }