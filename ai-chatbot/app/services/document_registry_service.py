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

    cur.execute("PRAGMA table_info(managed_documents)")
    columns = [row[1] for row in cur.fetchall()]

    if "document_key" not in columns:
        cur.execute("ALTER TABLE managed_documents ADD COLUMN document_key TEXT")

    if "is_active" not in columns:
        cur.execute("ALTER TABLE managed_documents ADD COLUMN is_active INTEGER DEFAULT 0")

    if "parent_document_id" not in columns:
        cur.execute("ALTER TABLE managed_documents ADD COLUMN parent_document_id INTEGER")

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
    document_key = f"{title}:{category or ''}"

    cur.execute(
        """
        INSERT INTO managed_documents (
            title, category, original_name, saved_name, storage_path,
            mime_type, file_extension, file_category, file_size,
            parsed_text, version, status, approved_by, approved_at,
            created_at, updated_at, document_key, is_active, parent_document_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            now,
            document_key,
            0,
            None,
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


def get_session_document(document_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM session_documents
        WHERE id = ?
    """, (document_id,))

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None


def get_managed_document(document_id: int) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM managed_documents
        WHERE id = ?
    """, (document_id,))

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None


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


def update_managed_document_processing(
    document_id: int,
    status: str,
    parsed_text: str | None = None
):
    conn = get_conn()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        UPDATE managed_documents
        SET status = ?, parsed_text = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, parsed_text, now, document_id)
    )

    conn.commit()
    conn.close()

def get_parsed_session_documents(conversation_id: int) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, original_name, parsed_text, ocr_text, vision_summary
        FROM session_documents
        WHERE conversation_id = ?
          AND doc_status = 'parsed'
        ORDER BY id DESC
        """,
        (conversation_id,)
    )

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        parsed_text = row["parsed_text"] or ""
        ocr_text = row["ocr_text"] or ""
        vision_summary = row["vision_summary"] or ""

        merged_text_parts = []
        if parsed_text.strip():
            merged_text_parts.append(parsed_text.strip())
        if ocr_text.strip():
            merged_text_parts.append(ocr_text.strip())
        if vision_summary.strip():
            merged_text_parts.append(vision_summary.strip())

        merged_text = "\n".join(merged_text_parts).strip()

        results.append({
            "id": row["id"],
            "source": row["original_name"],
            "content": merged_text,
            "chunk_index": 0,
            "search_type": "session"
        })

    return results

def get_approved_managed_documents() -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM managed_documents
        WHERE status IN ('approved', 'parsed')
        ORDER BY id DESC
        """
    )

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def mark_managed_document_indexed(document_id: int):
    conn = get_conn()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        UPDATE managed_documents
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        ("indexed", now, document_id)
    )

    conn.commit()
    conn.close()

def delete_managed_document(document_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM managed_documents
        WHERE id = ?
        """,
        (document_id,)
    )

    conn.commit()
    conn.close()


def activate_managed_document(document_id: int):
    document = get_managed_document(document_id)

    if not document:
        raise ValueError(f"관리 문서를 찾을 수 없습니다: {document_id}")

    document_key = document.get("document_key")

    conn = get_conn()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    if document_key:
        cur.execute(
            """
            UPDATE managed_documents
            SET is_active = 0,
                status = CASE
                    WHEN id != ? AND status = 'indexed' THEN 'retired'
                    ELSE status
                END,
                updated_at = ?
            WHERE document_key = ?
            """,
            (document_id, now, document_key)
        )

    cur.execute(
        """
        UPDATE managed_documents
        SET is_active = 1,
            status = 'indexed',
            updated_at = ?
        WHERE id = ?
        """,
        (now, document_id)
    )

    conn.commit()
    conn.close()


def _parse_version_number(version: str | None) -> int:
    if not version:
        return 1

    cleaned = str(version).lower().replace("v", "").strip()

    try:
        return int(cleaned)
    except ValueError:
        return 1


def create_managed_document_version(
    parent_document_id: int,
    original_name: str,
    saved_name: str,
    storage_path: str,
    mime_type: str,
    file_extension: str,
    file_category: str,
    file_size: int,
) -> int:
    parent = get_managed_document(parent_document_id)

    if not parent:
        raise ValueError(f"기준 문서를 찾을 수 없습니다: {parent_document_id}")

    title = parent["title"]
    category = parent["category"]
    document_key = parent.get("document_key") or f"{title}:{category or ''}"

    current_version_no = _parse_version_number(parent.get("version"))
    next_version = f"v{current_version_no + 1}"

    conn = get_conn()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO managed_documents (
            title, category, original_name, saved_name, storage_path,
            mime_type, file_extension, file_category, file_size,
            parsed_text, version, status, approved_by, approved_at,
            created_at, updated_at, document_key, is_active, parent_document_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            next_version,
            "draft",
            None,
            None,
            now,
            now,
            document_key,
            0,
            parent_document_id,
        ),
    )

    doc_id = cur.lastrowid
    conn.commit()
    conn.close()

    return doc_id