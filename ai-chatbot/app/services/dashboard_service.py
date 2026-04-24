import sqlite3
from pathlib import Path

APP_DB_PATH = Path("data/app_state.db")
CHAT_DB_PATH = Path("data/chat_history.db")


def _count_rows(db_path: Path, table_name: str) -> int:
    if not db_path.exists():
        return 0

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
    except Exception:
        count = 0

    conn.close()
    return count


def _count_by_status(db_path: Path, table_name: str, status_col: str, status: str) -> int:
    if not db_path.exists():
        return 0

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE {status_col} = ?",
            (status,),
        )
        count = cur.fetchone()[0]
    except Exception:
        count = 0

    conn.close()
    return count


def _recent_managed_documents(limit: int = 5) -> list[dict]:
    if not APP_DB_PATH.exists():
        return []

    conn = sqlite3.connect(APP_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id, title, category, original_name, status, created_at, updated_at
            FROM managed_documents
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
    except Exception:
        rows = []

    conn.close()
    return [dict(row) for row in rows]


def get_dashboard_summary() -> dict:
    total_conversations = _count_rows(CHAT_DB_PATH, "conversations")
    total_messages = _count_rows(CHAT_DB_PATH, "messages")

    total_session_documents = _count_rows(APP_DB_PATH, "session_documents")
    parsed_session_documents = _count_by_status(
        APP_DB_PATH, "session_documents", "doc_status", "parsed"
    )

    total_managed_documents = _count_rows(APP_DB_PATH, "managed_documents")
    indexed_managed_documents = _count_by_status(
        APP_DB_PATH, "managed_documents", "status", "indexed"
    )
    failed_managed_documents = _count_by_status(
        APP_DB_PATH, "managed_documents", "status", "failed"
    )

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_session_documents": total_session_documents,
        "parsed_session_documents": parsed_session_documents,
        "total_managed_documents": total_managed_documents,
        "indexed_managed_documents": indexed_managed_documents,
        "failed_managed_documents": failed_managed_documents,
        "recent_managed_documents": _recent_managed_documents(),
    }