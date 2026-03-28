from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from usermanagement.models import Role, User


class UserRepository:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    @contextmanager
    def _connection(self) -> Iterable[sqlite3.Connection]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login_at TEXT
                );
                """
            )

    def create_user(self, email: str, full_name: str, role: Role, password_hash: str) -> User:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (email, full_name, role, password_hash, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (email.lower(), full_name.strip(), role.value, password_hash, now, now),
            )
            user_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _row_to_user(row)

    def get_user_by_email(self, email: str) -> Optional[dict]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email.lower(),),
            ).fetchone()
            return dict(row) if row else None

    def get_user(self, user_id: int) -> Optional[User]:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _row_to_user(row) if row else None

    def list_users(self, role: Optional[Role] = None, active_only: bool = True) -> list[User]:
        query = "SELECT * FROM users WHERE 1=1"
        params: list[object] = []

        if role:
            query += " AND role = ?"
            params.append(role.value)

        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY full_name ASC"

        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [_row_to_user(row) for row in rows]

    def update_role(self, user_id: int, role: Role) -> Optional[User]:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._connection() as conn:
            conn.execute(
                "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
                (role.value, now, user_id),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _row_to_user(row) if row else None

    def set_active_status(self, user_id: int, is_active: bool) -> Optional[User]:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._connection() as conn:
            conn.execute(
                "UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?",
                (1 if is_active else 0, now, user_id),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _row_to_user(row) if row else None

    def update_last_login(self, user_id: int) -> Optional[User]:
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._connection() as conn:
            conn.execute(
                "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
                (now, now, user_id),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _row_to_user(row) if row else None


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        role=Role(row["role"]),
        is_active=bool(row["is_active"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        last_login_at=datetime.fromisoformat(row["last_login_at"]) if row["last_login_at"] else None,
    )
