import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class NotificationStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notified_items (
                id TEXT PRIMARY KEY,
                item_id TEXT,
                query_name TEXT,
                title TEXT,
                notified_at TEXT,
                extra TEXT
            )
            """
        )
        self.conn.commit()

    def was_notified(self, key: str) -> bool:
        cursor = self.conn.execute("SELECT 1 FROM notified_items WHERE id = ?", (key,))
        return cursor.fetchone() is not None

    def mark_notified(self, key: str, item: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO notified_items (id, item_id, query_name, title, notified_at, extra) VALUES (?, ?, ?, ?, ?, ?)",
            (
                key,
                str(item.get("id", "")),
                item.get("query_name", ""),
                item.get("title", ""),
                datetime.utcnow().isoformat() + "Z",
                str(item),
            ),
        )
        self.conn.commit()
