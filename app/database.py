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
