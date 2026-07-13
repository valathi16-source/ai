import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "chat.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_message(role: str, content: str):
    conn = get_connection()
    conn.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()


def get_history(limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM messages ORDER BY id ASC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def clear_history():
    conn = get_connection()
    conn.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
