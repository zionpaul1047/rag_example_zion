from pathlib import Path
from pypdf import PdfReader

from app.core.settings import settings
from app.services.ocr_service import extract_text_from_pdf_with_ocr
from app.services.parsers.base_parser import BaseParser


class PdfParser(BaseParser):
    def parse(self, file_path: Path) -> dict:
        reader = PdfReader(str(file_path))
        pages = []

        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())

        content = "\n\n".join(pages).strip()

        used_ocr = False

        if settings.OCR_ENABLED and len(content) < settings.OCR_MIN_TEXT_LENGTH:
            ocr_text = extract_text_from_pdf_with_ocr(str(file_path))
            if ocr_text.strip():
                content = ocr_text
                used_ocr = True

        return {
            "source": file_path.name,
            "content": content,
            "file_type": "pdf",
            "used_ocr": used_ocr
        }