from pathlib import Path
from app.services.parsers.text_parser import TextParser
from app.services.parsers.markdown_parser import MarkdownParser
from app.services.parsers.html_parser import HtmlParser
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.docx_parser import DocxParser


def get_parser(file_path: Path):
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return TextParser()

    if suffix == ".md":
        return MarkdownParser()

    if suffix in [".html", ".htm"]:
        return HtmlParser()

    if suffix == ".pdf":
        return PdfParser()

    if suffix == ".docx":
        return DocxParser()

    raise ValueError(f"지원하지 않는 파일 형식입니다: {file_path.name}")