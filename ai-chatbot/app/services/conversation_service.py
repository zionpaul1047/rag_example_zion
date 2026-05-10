import json
import sqlite3
from pathlib import Path
from typing import Any

from app.services import document_registry_service
from app.services.file_storage_service import delete_stored_file

DB_PATH = Path("data/chat_history.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_table_names(cur: sqlite3.Cursor) -> set[str]:
    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """)
    return {row["name"] for row in cur.fetchall()}


def _get_columns(cur: sqlite3.Cursor, table_name: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row["name"] for row in cur.fetchall()}


def _parse_metadata(raw_metadata: str | None) -> dict[str, Any]:
    if not raw_metadata:
        return {}

    try:
        parsed = json.loads(raw_metadata)
    except json.JSONDecodeError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _owned_conversation_exists(
    cur: sqlite3.Cursor,
    conversation_id: int,
    username: str | None,
) -> bool:
    table_names = _get_table_names(cur)
    if "conversations" not in table_names:
        return False

    conversation_columns = _get_columns(cur, "conversations")
    if username and "username" in conversation_columns:
        cur.execute("""
            SELECT id
            FROM conversations
            WHERE id = ?
              AND (username = ? OR username IS NULL)
        """, (conversation_id, username))
    else:
        cur.execute("""
            SELECT id
            FROM conversations
            WHERE id = ?
        """, (conversation_id,))

    return cur.fetchone() is not None


def _cleanup_session_documents(conversation_id: int) -> dict:
    try:
        documents = document_registry_service.list_session_documents(conversation_id)
    except sqlite3.OperationalError:
        return {
            "session_document_count": 0,
            "session_file_deleted_count": 0,
            "session_cleanup_errors": [],
        }

    file_deleted_count = 0
    cleanup_errors = []

    for document in documents:
        document_id = document["id"]

        try:
            if delete_stored_file(document["storage_path"], scope="session"):
                file_deleted_count += 1
        except Exception as e:
            cleanup_errors.append({
                "document_id": document_id,
                "stage": "file",
                "error": str(e),
            })

        try:
            document_registry_service.delete_session_document(document_id)
        except Exception as e:
            cleanup_errors.append({
                "document_id": document_id,
                "stage": "registry",
                "error": str(e),
            })

    return {
        "session_document_count": len(documents),
        "session_file_deleted_count": file_deleted_count,
        "session_cleanup_errors": cleanup_errors,
    }


def conversation_belongs_to_user(
    conversation_id: int,
    username: str | None,
) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    try:
        return _owned_conversation_exists(cur, conversation_id, username)
    finally:
        cur.close()
        conn.close()


def list_conversations(username: str | None = None) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    try:
        table_names = _get_table_names(cur)

        if "conversations" not in table_names:
            return []

        conversation_columns = _get_columns(cur, "conversations")
        has_username = "username" in conversation_columns
        username_select = "c.username AS username" if has_username else "NULL AS username"
        username_group = ", c.username" if has_username else ""
        where_clause = ""
        params = ()

        if username and has_username:
            where_clause = "WHERE c.username = ? OR c.username IS NULL"
            params = (username,)

        if "messages" in table_names:
            cur.execute(f"""
                SELECT
                    c.id AS id,
                    c.created_at AS created_at,
                    {username_select},
                    COALESCE(MAX(m.created_at), c.created_at) AS updated_at,
                    COALESCE(
                        NULLIF(c.title, ''),
                        (
                            SELECT m2.content
                            FROM messages m2
                            WHERE m2.conversation_id = c.id
                              AND m2.role = 'user'
                            ORDER BY m2.id ASC
                            LIMIT 1
                        ),
                        '새 대화'
                    ) AS title,
                    COUNT(m.id) AS message_count
                FROM conversations c
                LEFT JOIN messages m ON m.conversation_id = c.id
                {where_clause}
                GROUP BY c.id, c.created_at, c.title{username_group}
                ORDER BY COALESCE(MAX(m.created_at), c.created_at) DESC
            """, params)
        else:
            username_select = "username" if has_username else "NULL AS username"
            where_clause = ""
            params = ()

            if username and has_username:
                where_clause = "WHERE username = ? OR username IS NULL"
                params = (username,)

            cur.execute(f"""
                SELECT
                    id,
                    created_at,
                    {username_select},
                    created_at AS updated_at,
                    COALESCE(NULLIF(title, ''), '새 대화') AS title,
                    0 AS message_count
                FROM conversations
                {where_clause}
                ORDER BY id DESC
            """, params)

        rows = cur.fetchall()

        results = []
        for row in rows:
            title = row["title"] or "새 대화"
            title = " ".join(str(title).split())

            if len(title) > 40:
                title = title[:40] + "..."

            results.append({
                "id": row["id"],
                "title": title,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "username": row["username"],
                "message_count": row["message_count"],
            })

        return results
    finally:
        cur.close()
        conn.close()


def get_conversation_messages(
    conversation_id: int,
    username: str | None = None,
) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    try:
        table_names = _get_table_names(cur)

        if "messages" not in table_names:
            return []

        if username and not _owned_conversation_exists(cur, conversation_id, username):
            return []

        message_columns = _get_columns(cur, "messages")
        metadata_select = "metadata" if "metadata" in message_columns else "NULL AS metadata"

        cur.execute(f"""
            SELECT
                id,
                conversation_id,
                role,
                content,
                created_at,
                {metadata_select}
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
        """, (conversation_id,))

        rows = cur.fetchall()

        messages = []
        for row in rows:
            item = dict(row)
            metadata = _parse_metadata(item.pop("metadata", None))
            item["metadata"] = metadata
            item["sources"] = metadata.get("sources", [])
            messages.append(item)

        return messages
    finally:
        cur.close()
        conn.close()


def delete_conversation(
    conversation_id: int,
    username: str | None = None,
) -> dict:
    conn = get_conn()
    cur = conn.cursor()

    try:
        table_names = _get_table_names(cur)

        if "conversations" not in table_names:
            return {
                "deleted": False,
                "conversation_id": conversation_id,
                "message_count": 0,
                "session_document_count": 0,
                "session_file_deleted_count": 0,
                "session_cleanup_errors": [],
            }

        if username and not _owned_conversation_exists(cur, conversation_id, username):
            return {
                "deleted": False,
                "conversation_id": conversation_id,
                "message_count": 0,
                "session_document_count": 0,
                "session_file_deleted_count": 0,
                "session_cleanup_errors": [],
            }

        session_cleanup = _cleanup_session_documents(conversation_id)

        if "messages" in table_names:
            cur.execute(
                "SELECT COUNT(*) AS count FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            message_count = cur.fetchone()["count"]

            cur.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            )
        else:
            message_count = 0

        cur.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        deleted = cur.rowcount > 0

        conn.commit()

        return {
            "deleted": deleted,
            "conversation_id": conversation_id,
            "message_count": message_count,
            **session_cleanup,
        }
    finally:
        cur.close()
        conn.close()
