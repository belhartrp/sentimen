import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "storage" / "app.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                row_count INTEGER DEFAULT 0,
                text_column TEXT,
                label_column TEXT,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                uploaded_by INTEGER,
                FOREIGN KEY(uploaded_by) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                algorithm TEXT NOT NULL,
                test_size REAL NOT NULL,
                metrics_json TEXT NOT NULL,
                labels_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id)
            )
            """
        )
        cur.execute(
            """
            INSERT OR IGNORE INTO users (id, name, email, password)
            VALUES (1, 'Admin', 'admin@example.com', 'admin123')
            """
        )
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def fetch_all(query: str, params: Iterable[Any] = ()):
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def fetch_one(query: str, params: Iterable[Any] = ()):
    with get_conn() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def execute(query: str, params: Iterable[Any] = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid


def dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)
