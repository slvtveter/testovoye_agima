import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent / "history.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            model_used TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            summary TEXT NOT NULL DEFAULT '',
            summarized_up_to_id INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO conversation_state (id, summary, summarized_up_to_id) VALUES (1, '', 0)"
    )
    conn.commit()
    conn.close()


def save_query(question: str, answer: str, model_used: str) -> dict:
    conn = get_connection()
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO queries (question, answer, model_used, created_at) VALUES (?, ?, ?, ?)",
        (question, answer, model_used, created_at),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return {
        "id": row_id,
        "question": question,
        "answer": answer,
        "model_used": model_used,
        "created_at": created_at,
    }


def get_last_queries(limit: int = 5) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, question, answer, model_used, created_at FROM queries ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_conversation_state() -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT summary, summarized_up_to_id FROM conversation_state WHERE id = 1"
    ).fetchone()
    conn.close()
    return dict(row)


def update_conversation_state(summary: str, summarized_up_to_id: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE conversation_state SET summary = ?, summarized_up_to_id = ? WHERE id = 1",
        (summary, summarized_up_to_id),
    )
    conn.commit()
    conn.close()


def get_queries_after(query_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, question, answer FROM queries WHERE id > ? ORDER BY id ASC",
        (query_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
