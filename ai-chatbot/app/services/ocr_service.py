from io import BytesIO
import fitz
import easyocr
from PIL import Image

from app.core.settings import settings

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        langs = [lang.strip() for lang in settings.OCR_LANG_LIST.split(",") if lang.strip()]
        _reader = easyocr.Reader(langs, gpu=False)
    return _reader


def extract_text_from_pdf_with_ocr(file_path: str) -> str:
    reader = _get_reader()
    doc = fitz.open(file_path)

    try:
        page_texts = []

        for page in doc:
            zoom = settings.OCR_RENDER_DPI / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            image_bytes = pix.tobytes("png")
            image = Image.open(BytesIO(image_bytes))

            results = reader.readtext(image_bytes, detail=0, paragraph=True)

            lines = []
            for item in results:
                text = str(item).strip()
                if text:
                    lines.append(text)

            page_text = "\n".join(lines).strip()
            if page_text:
                page_texts.append(page_text)

        return "\n\n".join(page_texts).strip()

    finally:
        doc.close()