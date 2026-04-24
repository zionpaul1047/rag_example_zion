import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/chat_history.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def setup_chat_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        title TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 기존 DB에 title 컬럼 없을 경우 추가
    cur.execute("PRAGMA table_info(conversations)")
    columns = [row[1] for row in cur.fetchall()]

    if "title" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN title TEXT")

    conn.commit()
    conn.close()


def create_conversation() -> int:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO conversations (created_at) VALUES (?)",
        (datetime.utcnow().isoformat(),)
    )

    conversation_id = cur.lastrowid

    conn.commit()
    conn.close()

    return conversation_id


def add_message(conversation_id: int, role: str, content: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content,
            datetime.utcnow().isoformat()
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