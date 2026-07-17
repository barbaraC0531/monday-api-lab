from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class ConversationRecord:
    conversation_id: str
    created_at: datetime


@dataclass(frozen=True)
class MessageRecord:
    message_id: str
    conversation_id: str
    role: str
    text: str
    created_at: datetime
    model_response_id: str | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


class ConversationRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        if self.database_path.parent != Path(""):
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    model_response_id TEXT,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at)")

    def create_conversation(self) -> ConversationRecord:
        record = ConversationRecord(str(uuid4()), _utc_now())
        with self.connect() as conn:
            conn.execute("INSERT INTO conversations VALUES (?, ?)", (record.conversation_id, record.created_at.isoformat()))
        return record

    def get_conversation(self, conversation_id: str) -> ConversationRecord | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,)).fetchone()
        return ConversationRecord(row["conversation_id"], _parse_dt(row["created_at"])) if row else None

    def add_message(self, conversation_id: str, role: str, text: str, model_response_id: str | None = None) -> MessageRecord:
        record = MessageRecord(str(uuid4()), conversation_id, role, text, _utc_now(), model_response_id)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
                (record.message_id, conversation_id, role, text, record.created_at.isoformat(), model_response_id),
            )
        return record

    def list_messages(self, conversation_id: str, limit: int | None = None) -> list[MessageRecord]:
        sql = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC"
        params: tuple[object, ...] = (conversation_id,)
        if limit is not None:
            sql += " LIMIT ?"
            params = (conversation_id, limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [MessageRecord(r["message_id"], r["conversation_id"], r["role"], r["text"], _parse_dt(r["created_at"]), r["model_response_id"]) for r in rows]
