import sqlite3
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends

from app.core.settings import settings
from app.api.dependencies import require_admin_user

router = APIRouter()

DB_PATH = Path("data/chat_history.db")
DOC_DB_PATH = Path(settings.APP_SQLITE_PATH)


def get_chat_conn():
    return sqlite3.connect(DB_PATH)


def get_doc_conn():
    return sqlite3.connect(DOC_DB_PATH)


@router.get("/admin/dashboard")
def get_dashboard(_admin: dict = Depends(require_admin_user)):
    result = {
        "conversation_count": 0,
        "today_conversation_count": 0,
        "message_count": 0,
        "managed_doc_count": 0,
        "active_doc_count": 0,
        "retired_doc_count": 0,
        "recent_conversations": [],
        "recent_documents": [],
        "status_summary": {},
    }

    # Chat DB
    try:
        conn = get_chat_conn()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM conversations")
        result["conversation_count"] = cur.fetchone()[0]

        today = datetime.utcnow().strftime("%Y-%m-%d")

        cur.execute(
            """
            SELECT COUNT(*)
            FROM conversations
            WHERE substr(created_at,1,10)=?
            """,
            (today,),
        )
        result["today_conversation_count"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM messages")
        result["message_count"] = cur.fetchone()[0]

        cur.execute(
            """
            SELECT id, created_at
            FROM conversations
            ORDER BY id DESC
            LIMIT 5
            """
        )

        rows = cur.fetchall()

        for row in rows:
            result["recent_conversations"].append(
                {
                    "id": row[0],
                    "created_at": row[1],
                }
            )

        conn.close()

    except Exception:
        pass

    # Document DB
    try:
        conn = get_doc_conn()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM managed_documents")
        result["managed_doc_count"] = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*)
            FROM managed_documents
            WHERE is_active=1
            """
        )
        result["active_doc_count"] = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*)
            FROM managed_documents
            WHERE status='retired'
            """
        )
        result["retired_doc_count"] = cur.fetchone()[0]

        cur.execute(
            """
            SELECT status, COUNT(*)
            FROM managed_documents
            GROUP BY status
            """
        )

        for row in cur.fetchall():
            result["status_summary"][row[0]] = row[1]

        cur.execute(
            """
            SELECT id, title, version, status, created_at
            FROM managed_documents
            ORDER BY id DESC
            LIMIT 5
            """
        )

        rows = cur.fetchall()

        for row in rows:
            result["recent_documents"].append(
                {
                    "id": row[0],
                    "title": row[1],
                    "version": row[2],
                    "status": row[3],
                    "created_at": row[4],
                }
            )

        conn.close()

    except Exception:
        pass

    return result
