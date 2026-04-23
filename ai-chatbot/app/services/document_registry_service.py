import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from app.core.settings import settings

DB_PATH = Path(settings.APP_SQLITE_PATH)


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup_document_registry():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS session_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        conversation_id INTEGER,
        original_name TEXT NOT NULL,
        saved_name TEXT NOT NULL,
        storage_path TEXT NOT NULL,
        mime_type TEXT,
        file_extension TEXT,
        file_category TEXT,
        file_size INTEGER,
        ocr_text TEXT,
        vision_summary TEXT,
        parsed_text TEXT,
        doc_status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS managed_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT,
        original_name TEXT NOT NULL,
        saved_name TEXT NOT NULL,
        storage_path TEXT NOT NULL,
        mime_type TEXT,
        file_extension TEXT,
        file_category TEXT,
        file_size INTEGER,
        parsed_text TEXT,
        version TEXT,
        status TEXT NOT NULL,
        approved_by TEXT,
        approved_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def create_session_document(
    user_id: str | None,
    conversation_id: int | None,
    original_name: str,
    saved_name: str,
    storage_path: str,
    mime_type: str,
    file_extension: str,
    file_category: str,
    file_size: int,
) -> int:
    conn = get_conn()
    cur = conn.cursor()

    now = datetime.utcnow()
    expires_at = now + timedelta(days=settings.SESSION_FILE_TTL_DAYS)

    cur.execute(
        """
        INSERT INTO session_documents (
            user_id, conversation_id, original_name, saved_name, storage_path,
            mime_type, file_extension, file_category, file_size,
            ocr_text, vision_summary, parsed_text, doc_status,
            created_at, expires_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            conversation_id,
            original_name,
            saved_name,
            storage_path,
            mime_type,
            file_extension,
            file_category,
            file_size,
            None,
            None,
            None,
            "uploaded",
            now.isoformat(),
            expires_at.isoformat()
        )
    )

    doc_id = cur.lastrowid
    conn.commit()
    conn.close()

    return doc_id


def create_managed_document(
    title: str,
    category: str | None,
    original_name: str,
    saved_name: str,
    storage_path: str,
    mime_type: str,
    file_extension: str,
    file_category: str,
    file_size: int,
) -> int:
    conn = get_conn()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO managed_documents (
            title, category, original_name, saved_name, storage_path,
            mime_type, file_extension, file_category, file_size,
            parsed_text, version, status, approved_by, approved_at,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            category,
            original_name,
            saved_name,
            storage_path,
            mime_type,
            file_extension,
            file_category,
            file_size,
            None,
            "v1",
            "draft",
            None,
            None,
            now,
            now
        )
    )

    doc_id = cur.lastrowid
    conn.commit()
    conn.close()

    return doc_id


def list_session_documents(conversation_id: int | None = None) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    if conversation_id is None:
        cur.execute("""
            SELECT * FROM session_documents
            ORDER BY id DESC
        """)
    else:
        cur.execute("""
            SELECT * FROM session_documents
            WHERE conversation_id = ?
            ORDER BY id DESC
        """, (conversation_id,))

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def list_managed_documents() -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM managed_documents
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def approve_managed_document(document_id: int, approved_by: str | None = None):
    conn = get_conn()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        UPDATE managed_documents
        SET status = ?, approved_by = ?, approved_at = ?, updated_at = ?
        WHERE id = ?
        """,
        ("approved", approved_by, now, now, document_id)
    )

    conn.commit()
    conn.close()


def update_session_document_processing(
    document_id: int,
    doc_status: str,
    ocr_text: str | None = None,
    vision_summary: str | None = None,
    parsed_text: str | None = None
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE session_documents
        SET doc_status = ?, ocr_text = ?, vision_summary = ?, parsed_text = ?
        WHERE id = ?
        """,
        (doc_status, ocr_text, vision_summary, parsed_text, document_id)
    )

    conn.commit()
    conn.close()