import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any

DB_PATH = Path("data/chat_history.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _get_columns(cur: sqlite3.Cursor, table_name: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def setup_chat_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        title TEXT,
        username TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        metadata TEXT
    )
    """)

    conversation_columns = _get_columns(cur, "conversations")
    if "title" not in conversation_columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN title TEXT")
    if "username" not in conversation_columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN username TEXT")

    message_columns = _get_columns(cur, "messages")
    if "metadata" not in message_columns:
        cur.execute("ALTER TABLE messages ADD COLUMN metadata TEXT")

    conn.commit()
    conn.close()


def create_conversation(username: str | None = None) -> int:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO conversations (created_at, username) VALUES (?, ?)",
        (datetime.utcnow().isoformat(), username)
    )

    conversation_id = cur.lastrowid

    conn.commit()
    conn.close()

    return conversation_id


def add_message(
    conversation_id: int,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
):
    conn = get_conn()
    cur = conn.cursor()

    metadata_json = None
    if metadata:
        metadata_json = json.dumps(metadata, ensure_ascii=False, default=str)

    cur.execute(
        """
        INSERT INTO messages (conversation_id, role, content, created_at, metadata)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content,
            datetime.utcnow().isoformat(),
            metadata_json,
        )
    )

    conn.commit()
    conn.close()


def get_recent_messages(conversation_id: int, limit: int = 6) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (conversation_id, limit)
    )

    rows = cur.fetchall()
    conn.close()

    rows.reverse()

    return [{"role": row[0], "content": row[1]} for row in rows]


def update_conversation_title(conversation_id: int, title: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE conversations
        SET title = ?
        WHERE id = ?
        """,
        (title, conversation_id)
    )

    conn.commit()
    conn.close()
