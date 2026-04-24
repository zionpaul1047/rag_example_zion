import sqlite3
from pathlib import Path

DB_PATH = Path("data/chat_history.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_conversations(username: str | None = None) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """)
    table_names = {row["name"] for row in cur.fetchall()}

    if "conversations" not in table_names:
        conn.close()
        return []

    if "messages" in table_names:
        cur.execute("""
            SELECT
                c.id AS id,
                c.created_at AS created_at,
                COALESCE(MAX(m.created_at), c.created_at) AS updated_at,
                COALESCE(
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
            GROUP BY c.id, c.created_at
            ORDER BY COALESCE(MAX(m.created_at), c.created_at) DESC
        """)
    else:
        cur.execute("""
            SELECT
                id,
                created_at,
                created_at AS updated_at,
                '새 대화' AS title,
                0 AS message_count
            FROM conversations
            ORDER BY id DESC
        """)

    rows = cur.fetchall()
    conn.close()

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
            "message_count": row["message_count"],
        })

    return results


def get_conversation_messages(conversation_id: int) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """)
    table_names = {row["name"] for row in cur.fetchall()}

    if "messages" not in table_names:
        conn.close()
        return []

    cur.execute("""
        SELECT
            id,
            conversation_id,
            role,
            content,
            created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
    """, (conversation_id,))

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]