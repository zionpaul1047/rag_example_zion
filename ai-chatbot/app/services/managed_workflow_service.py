from datetime import datetime

from app.services.document_registry_service import (
    get_managed_document,
    update_managed_document_processing,
    delete_managed_document,
)


ALLOWED_TRANSITIONS = {
    "draft": ["parsed", "failed"],
    "parsed": ["review", "failed"],
    "review": ["approved", "parsed", "failed"],
    "approved": ["indexed", "review", "failed"],
    "indexed": ["retired"],
    "retired": ["indexed"],
    "failed": ["parsed"],
}


DELETABLE_STATUSES = {"draft", "parsed", "failed"}


def validate_transition(current_status: str, next_status: str):
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])

    if next_status not in allowed:
        raise ValueError(
            f"상태 변경 불가: {current_status} → {next_status}. "
            f"허용 상태: {allowed}"
        )


def change_managed_document_status(document_id: int, next_status: str) -> dict:
    document = get_managed_document(document_id)

    if not document:
        raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

    current_status = document["status"]

    validate_transition(current_status, next_status)

    update_managed_document_processing(
        document_id=document_id,
        status=next_status,
        parsed_text=document.get("parsed_text"),
    )

    return {
        "document_id": document_id,
        "previous_status": current_status,
        "next_status": next_status,
        "changed_at": datetime.utcnow().isoformat(),
    }


def delete_managed_document_if_allowed(document_id: int) -> dict:
    document = get_managed_document(document_id)

    if not document:
        raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

    current_status = document["status"]

    if current_status not in DELETABLE_STATUSES:
        raise ValueError(
            f"{current_status} 상태 문서는 삭제할 수 없습니다. "
            f"삭제 가능 상태: {sorted(DELETABLE_STATUSES)}"
        )

    delete_managed_document(document_id)

    return {
        "document_id": document_id,
        "deleted": True,
        "previous_status": current_status,
        "deleted_at": datetime.utcnow().isoformat(),
    }