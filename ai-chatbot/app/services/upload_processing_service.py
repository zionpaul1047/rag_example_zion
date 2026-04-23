from pathlib import Path

from app.core.settings import settings
from app.services.parsers.parser_factory import get_parser
from app.services.ocr_service import extract_text_from_image_with_ocr
from app.services.vision_service import analyze_image_with_vision
from app.services.document_registry_service import (
    get_session_document,
    get_managed_document,
    update_session_document_processing,
    update_managed_document_processing
)
from app.utils.text_cleaner import clean_text


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def _parse_document_file(file_path: Path) -> str:
    parser = get_parser(file_path)
    document = parser.parse(file_path)
    raw_text = document.get("content", "") or ""
    return clean_text(raw_text)


def _process_image_file(file_path: Path) -> tuple[str, str, str]:
    ocr_text = extract_text_from_image_with_ocr(str(file_path))
    vision_summary = ""

    if settings.VISION_ENABLED:
        try:
            vision_summary = analyze_image_with_vision(str(file_path))
        except Exception as e:
            print(f"[VISION] 이미지 비전 분석 실패: {e}")
            vision_summary = ""

    merged_parts = []
    if ocr_text.strip():
        merged_parts.append(ocr_text.strip())
    if vision_summary.strip():
        merged_parts.append(vision_summary.strip())

    parsed_text = clean_text("\n".join(merged_parts))
    return ocr_text, vision_summary, parsed_text


def process_session_document(document_id: int) -> dict:
    document = get_session_document(document_id)
    if not document:
        raise ValueError(f"세션 문서를 찾을 수 없습니다: {document_id}")

    file_path = Path(document["storage_path"])
    if not file_path.exists():
        update_session_document_processing(document_id, doc_status="failed")
        raise FileNotFoundError(f"저장 파일이 존재하지 않습니다: {file_path}")

    ext = file_path.suffix.lower()

    try:
        if ext in IMAGE_EXTENSIONS:
            ocr_text, vision_summary, parsed_text = _process_image_file(file_path)
            status = "parsed" if parsed_text else "failed"

            update_session_document_processing(
                document_id=document_id,
                doc_status=status,
                ocr_text=ocr_text or None,
                vision_summary=vision_summary or None,
                parsed_text=parsed_text or None
            )

            return {
                "id": document_id,
                "scope": "session",
                "file_type": "image",
                "doc_status": status,
                "ocr_length": len(ocr_text or ""),
                "vision_length": len(vision_summary or ""),
                "parsed_length": len(parsed_text or "")
            }

        parsed_text = _parse_document_file(file_path)
        status = "parsed" if parsed_text else "failed"

        update_session_document_processing(
            document_id=document_id,
            doc_status=status,
            ocr_text=None,
            vision_summary=None,
            parsed_text=parsed_text or None
        )

        return {
            "id": document_id,
            "scope": "session",
            "file_type": "document",
            "doc_status": status,
            "parsed_length": len(parsed_text or "")
        }

    except Exception as e:
        update_session_document_processing(
            document_id=document_id,
            doc_status="failed",
            ocr_text=None,
            vision_summary=None,
            parsed_text=None
        )
        raise RuntimeError(f"세션 문서 처리 실패: {e}") from e


def process_managed_document(document_id: int) -> dict:
    document = get_managed_document(document_id)
    if not document:
        raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

    file_path = Path(document["storage_path"])
    if not file_path.exists():
        update_managed_document_processing(document_id, status="failed", parsed_text=None)
        raise FileNotFoundError(f"저장 파일이 존재하지 않습니다: {file_path}")

    try:
        parsed_text = _parse_document_file(file_path)
        status = "parsed" if parsed_text else "failed"

        update_managed_document_processing(
            document_id=document_id,
            status=status,
            parsed_text=parsed_text or None
        )

        return {
            "id": document_id,
            "scope": "managed",
            "status": status,
            "parsed_length": len(parsed_text or "")
        }

    except Exception as e:
        update_managed_document_processing(document_id, status="failed", parsed_text=None)
        raise RuntimeError(f"관리 문서 처리 실패: {e}") from e


def auto_process_session_document(document_id: int) -> dict:
    try:
        return process_session_document(document_id)
    except Exception as e:
        return {
            "id": document_id,
            "scope": "session",
            "doc_status": "failed",
            "error": str(e)
        }