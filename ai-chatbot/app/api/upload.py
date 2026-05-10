from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from app.schemas.upload import SessionUploadResponse, ManagedUploadResponse
from app.api.dependencies import require_authenticated_user, require_admin_user
from app.services.file_storage_service import save_upload_file
from app.services.document_registry_service import (
    setup_document_registry,
    create_session_document,
    create_managed_document,
    list_session_documents,
    list_managed_documents,
    get_session_document,
    delete_session_document,
    get_managed_document,
    approve_managed_document,
    create_managed_document_version,
)
from app.services.file_storage_service import delete_stored_file
from app.services.upload_processing_service import (
    process_session_document,
    process_managed_document,
    auto_process_session_document
)
from app.services.managed_indexing_service import index_managed_document
from app.services.managed_workflow_service import (
    change_managed_document_status,
    delete_managed_document_if_allowed,
    force_delete_managed_document,
)

router = APIRouter()


@router.on_event("startup")
def startup_registry():
    setup_document_registry()


@router.post("/session-files/upload", response_model=SessionUploadResponse)
def upload_session_file(
    file: UploadFile = File(...),
    conversation_id: int | None = Form(default=None),
    user_id: str | None = Form(default=None),
    user: dict = Depends(require_authenticated_user),
):
    try:
        saved = save_upload_file(file, scope="session")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    doc_id = create_session_document(
        user_id=user["username"],
        conversation_id=conversation_id,
        original_name=saved["original_name"],
        saved_name=saved["saved_name"],
        storage_path=saved["saved_path"],
        mime_type=saved["mime_type"],
        file_extension=saved["file_extension"],
        file_category=saved["file_category"],
        file_size=saved["file_size"],
    )

    auto_result = auto_process_session_document(doc_id)
    final_status = auto_result.get("doc_status", "uploaded")

    return SessionUploadResponse(
        id=doc_id,
        scope="session",
        original_name=saved["original_name"],
        file_category=saved["file_category"],
        doc_status=final_status,
        conversation_id=conversation_id
    )


@router.get("/session-files")
def get_session_files(
    conversation_id: int | None = None,
    user: dict = Depends(require_authenticated_user),
):
    return list_session_documents(
        conversation_id=conversation_id,
        user_id=user["username"],
    )


@router.post("/session-files/{document_id}/process")
def process_uploaded_session_file(
    document_id: int,
    user: dict = Depends(require_authenticated_user),
):
    document = get_session_document(document_id, user_id=user["username"])

    if not document:
        raise HTTPException(status_code=404, detail="세션 문서를 찾을 수 없습니다.")

    try:
        return process_session_document(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/session-files/{document_id}")
def delete_uploaded_session_file(
    document_id: int,
    user: dict = Depends(require_authenticated_user),
):
    document = get_session_document(document_id, user_id=user["username"])

    if not document:
        raise HTTPException(status_code=404, detail="세션 문서를 찾을 수 없습니다.")

    try:
        file_deleted = delete_stored_file(document["storage_path"], scope="session")
        delete_session_document(document_id)

        return {
            "document_id": document_id,
            "deleted": True,
            "file_deleted": file_deleted,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/admin/rag-documents/upload", response_model=ManagedUploadResponse)
def upload_managed_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str | None = Form(default=None),
    _admin: dict = Depends(require_admin_user),
):
    try:
        saved = save_upload_file(file, scope="managed")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    doc_id = create_managed_document(
        title=title,
        category=category,
        original_name=saved["original_name"],
        saved_name=saved["saved_name"],
        storage_path=saved["saved_path"],
        mime_type=saved["mime_type"],
        file_extension=saved["file_extension"],
        file_category=saved["file_category"],
        file_size=saved["file_size"],
    )

    return ManagedUploadResponse(
        id=doc_id,
        scope="managed",
        title=title,
        category=category,
        original_name=saved["original_name"],
        file_category=saved["file_category"],
        status="draft"
    )


@router.post("/admin/rag-documents/{parent_document_id}/versions/upload")
def upload_managed_document_version(
    parent_document_id: int,
    file: UploadFile = File(...),
    _admin: dict = Depends(require_admin_user),
):
    try:
        parent = get_managed_document(parent_document_id)

        if not parent:
            raise ValueError(f"기준 문서를 찾을 수 없습니다: {parent_document_id}")

        saved = save_upload_file(file, scope="managed")

        doc_id = create_managed_document_version(
            parent_document_id=parent_document_id,
            original_name=saved["original_name"],
            saved_name=saved["saved_name"],
            storage_path=saved["saved_path"],
            mime_type=saved["mime_type"],
            file_extension=saved["file_extension"],
            file_category=saved["file_category"],
            file_size=saved["file_size"],
        )

        created = get_managed_document(doc_id)

        return {
            "message": "새 버전 업로드 완료",
            "id": doc_id,
            "parent_document_id": parent_document_id,
            "title": created["title"],
            "category": created["category"],
            "original_name": created["original_name"],
            "version": created["version"],
            "status": created["status"],
            "document_key": created.get("document_key"),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/admin/rag-documents")
def get_managed_documents(_admin: dict = Depends(require_admin_user)):
    return list_managed_documents()


@router.post("/admin/rag-documents/{document_id}/approve")
def approve_document(
    document_id: int,
    approved_by: str | None = Form(default=None),
    _admin: dict = Depends(require_admin_user),
):
    try:
        document = get_managed_document(document_id)

        if not document:
            raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

        if document["status"] != "review":
            raise ValueError("review 상태의 문서만 승인할 수 있습니다.")

        approve_managed_document(document_id=document_id, approved_by=approved_by)

        return {
            "message": "승인 완료",
            "document_id": document_id,
            "approved_by": approved_by
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/admin/rag-documents/{document_id}/process")
def process_uploaded_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        return process_managed_document(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/admin/rag-documents/{document_id}/index")
def index_uploaded_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        document = get_managed_document(document_id)

        if not document:
            raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

        if document["status"] != "approved":
            raise ValueError("approved 상태의 문서만 인덱싱할 수 있습니다.")

        return index_managed_document(document_id)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    

@router.post("/admin/rag-documents/{document_id}/request-review")
def request_review_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        return change_managed_document_status(document_id, "review")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/admin/rag-documents/{document_id}/retire")
def retire_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        return change_managed_document_status(document_id, "retired")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    

@router.post("/admin/rag-documents/{document_id}/rollback-review")
def rollback_review_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        return change_managed_document_status(document_id, "parsed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/admin/rag-documents/{document_id}/rollback-approve")
def rollback_approve_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        return change_managed_document_status(document_id, "review")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/admin/rag-documents/{document_id}/restore")
def restore_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        return change_managed_document_status(document_id, "indexed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/admin/rag-documents/{document_id}")
def delete_uploaded_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        return delete_managed_document_if_allowed(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/admin/rag-documents/{document_id}/force")
def force_delete_uploaded_managed_document(
    document_id: int,
    _admin: dict = Depends(require_admin_user),
):
    try:
        return force_delete_managed_document(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
