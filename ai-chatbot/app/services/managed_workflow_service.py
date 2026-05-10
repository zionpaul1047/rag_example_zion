from datetime import datetime

import psycopg
from elasticsearch import Elasticsearch

from app.core.settings import settings
from app.services.document_registry_service import (
    activate_managed_document,
    get_managed_document,
    get_latest_retired_managed_document,
    update_managed_document_processing,
    delete_managed_document,
)
from app.services.elasticsearch_index_service import INDEX_NAME
from app.services.file_storage_service import delete_stored_file


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

    file_deleted = delete_stored_file(document["storage_path"], scope="managed")
    delete_managed_document(document_id)

    return {
        "document_id": document_id,
        "deleted": True,
        "file_deleted": file_deleted,
        "previous_status": current_status,
        "deleted_at": datetime.utcnow().isoformat(),
    }


def _managed_source(document: dict) -> str:
    return f"[managed:{document['id']}]{document['original_name']}"


def delete_managed_document_vectors(document: dict) -> int:
    source = _managed_source(document)

    conn = psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        autocommit=True,
    )

    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM documents WHERE source = %s",
                (source,),
            )
            return cur.rowcount
    finally:
        conn.close()


def delete_managed_document_keyword_index(document: dict) -> int:
    source = _managed_source(document)
    es = Elasticsearch(settings.ELASTICSEARCH_HOST, request_timeout=30)

    response = es.delete_by_query(
        index=INDEX_NAME,
        query={
            "term": {
                "source": source,
            }
        },
        conflicts="proceed",
        refresh=True,
    )

    return int(response.get("deleted", 0))


def force_delete_managed_document(document_id: int) -> dict:
    document = get_managed_document(document_id)

    if not document:
        raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

    previous_status = document["status"]
    was_active = bool(document.get("is_active"))
    document_key = document.get("document_key")

    vector_deleted = 0
    keyword_deleted = 0
    restored_document = None

    if previous_status in {"indexed", "retired"} or document.get("is_active"):
        vector_deleted = delete_managed_document_vectors(document)
        keyword_deleted = delete_managed_document_keyword_index(document)

    file_deleted = delete_stored_file(document["storage_path"], scope="managed")
    delete_managed_document(document_id)

    if was_active and document_key:
        restored_document = get_latest_retired_managed_document(document_key)
        if restored_document:
            activate_managed_document(restored_document["id"])

    return {
        "document_id": document_id,
        "deleted": True,
        "forced": True,
        "file_deleted": file_deleted,
        "vector_deleted": vector_deleted,
        "keyword_deleted": keyword_deleted,
        "previous_status": previous_status,
        "restored_document_id": restored_document["id"] if restored_document else None,
        "deleted_at": datetime.utcnow().isoformat(),
    }
