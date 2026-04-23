from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.schemas.upload import SessionUploadResponse, ManagedUploadResponse
from app.services.file_storage_service import save_upload_file
from app.services.document_registry_service import (
    setup_document_registry,
    create_session_document,
    create_managed_document,
    list_session_documents,
    list_managed_documents,
    approve_managed_document
)
from app.services.upload_processing_service import (
    process_session_document,
    process_managed_document,
    auto_process_session_document
)
from app.services.managed_indexing_service import index_managed_document

router = APIRouter()


@router.on_event("startup")
def startup_registry():
    setup_document_registry()


@router.post("/session-files/upload", response_model=SessionUploadResponse)
def upload_session_file(
    file: UploadFile = File(...),
    conversation_id: int | None = Form(default=None),
    user_id: str | None = Form(default=None),
):
    try:
        saved = save_upload_file(file, scope="session")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    doc_id = create_session_document(
        user_id=user_id,
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
def get_session_files(conversation_id: int | None = None):
    return list_session_documents(conversation_id=conversation_id)


@router.post("/session-files/{document_id}/process")
def process_uploaded_session_file(document_id: int):
    try:
        return process_session_document(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/admin/rag-documents/upload", response_model=ManagedUploadResponse)
def upload_managed_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str | None = Form(default=None),
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


@router.get("/admin/rag-documents")
def get_managed_documents():
    return list_managed_documents()


@router.post("/admin/rag-documents/{document_id}/approve")
def approve_document(document_id: int, approved_by: str | None = Form(default=None)):
    approve_managed_document(document_id=document_id, approved_by=approved_by)
    return {
        "message": "승인 완료",
        "document_id": document_id,
        "approved_by": approved_by
    }


@router.post("/admin/rag-documents/{document_id}/process")
def process_uploaded_managed_document(document_id: int):
    try:
        return process_managed_document(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/admin/rag-documents/{document_id}/index")
def index_uploaded_managed_document(document_id: int):
    try:
        return index_managed_document(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e