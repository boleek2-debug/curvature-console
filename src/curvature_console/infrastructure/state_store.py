"""SQLite persistence for Curvature Console operational state."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from curvature_console.presentation.attachment_record import AttachmentRecord


@dataclass(frozen=True, slots=True)
class DepartmentState:
    """Persisted state for one department workspace."""

    conversation_text: str
    draft_text: str


@dataclass(frozen=True, slots=True)
class LayoutState:
    """Persisted main-window layout."""

    splitter_sizes: tuple[int, int, int]
    focused_department_id: str | None


@dataclass(frozen=True, slots=True)
class DepartmentChatRoute:
    """Persistent routing state for one department."""

    department_id: str
    project_name: str
    project_url: str
    active_conversation_url: str


@dataclass(frozen=True, slots=True)
class DepartmentChatHistoryEntry:
    """One previous or newly activated department conversation."""

    department_id: str
    conversation_url: str
    activated_at: str


class SQLiteStateStore:
    """Store Curvature Console state in SQLite."""

    def __init__(self, database_path: Path | None = None) -> None:
        if database_path is None:
            self.database_path: Path | None = None
            target = ":memory:"
        else:
            self.database_path = database_path.expanduser()
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            target = str(self.database_path)

        self._connection = sqlite3.connect(target)
        self._connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def close(self) -> None:
        self._connection.close()

    def save_department_state(
        self,
        department_id: str,
        conversation_text: str,
        draft_text: str,
    ) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO department_state (
                    department_id,
                    conversation_text,
                    draft_text
                )
                VALUES (?, ?, ?)
                ON CONFLICT(department_id) DO UPDATE SET
                    conversation_text = excluded.conversation_text,
                    draft_text = excluded.draft_text
                """,
                (department_id, conversation_text, draft_text),
            )

    def load_department_state(
        self,
        department_id: str,
    ) -> DepartmentState | None:
        row = self._connection.execute(
            """
            SELECT conversation_text, draft_text
            FROM department_state
            WHERE department_id = ?
            """,
            (department_id,),
        ).fetchone()

        if row is None:
            return None

        return DepartmentState(
            conversation_text=row["conversation_text"],
            draft_text=row["draft_text"],
        )

    def save_chat_route(
        self,
        department_id: str,
        project_name: str,
        project_url: str,
        active_conversation_url: str,
    ) -> None:
        """Persist active project and conversation routing."""

        timestamp = datetime.now(UTC).isoformat()
        with self._connection:
            previous = self._connection.execute(
                """
                SELECT active_conversation_url
                FROM department_chat_route
                WHERE department_id = ?
                """,
                (department_id,),
            ).fetchone()

            self._connection.execute(
                """
                INSERT INTO department_chat_route (
                    department_id,
                    project_name,
                    project_url,
                    active_conversation_url,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(department_id) DO UPDATE SET
                    project_name = excluded.project_name,
                    project_url = excluded.project_url,
                    active_conversation_url =
                        excluded.active_conversation_url,
                    updated_at = excluded.updated_at
                """,
                (
                    department_id,
                    project_name,
                    project_url,
                    active_conversation_url,
                    timestamp,
                ),
            )

            if (
                previous is None
                or previous["active_conversation_url"]
                != active_conversation_url
            ):
                self._connection.execute(
                    """
                    INSERT OR IGNORE INTO department_chat_history (
                        department_id,
                        conversation_url,
                        activated_at
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        department_id,
                        active_conversation_url,
                        timestamp,
                    ),
                )

    def load_chat_route(
        self,
        department_id: str,
    ) -> DepartmentChatRoute | None:
        row = self._connection.execute(
            """
            SELECT
                department_id,
                project_name,
                project_url,
                active_conversation_url
            FROM department_chat_route
            WHERE department_id = ?
            """,
            (department_id,),
        ).fetchone()

        if row is None:
            return None

        return DepartmentChatRoute(
            department_id=row["department_id"],
            project_name=row["project_name"],
            project_url=row["project_url"],
            active_conversation_url=row["active_conversation_url"],
        )

    def load_chat_history(
        self,
        department_id: str,
    ) -> tuple[DepartmentChatHistoryEntry, ...]:
        rows = self._connection.execute(
            """
            SELECT department_id, conversation_url, activated_at
            FROM department_chat_history
            WHERE department_id = ?
            ORDER BY activated_at
            """,
            (department_id,),
        ).fetchall()

        return tuple(
            DepartmentChatHistoryEntry(
                department_id=row["department_id"],
                conversation_url=row["conversation_url"],
                activated_at=row["activated_at"],
            )
            for row in rows
        )

    def save_layout(
        self,
        splitter_sizes: Iterable[int],
        focused_department_id: str | None,
    ) -> None:
        sizes = tuple(int(size) for size in splitter_sizes)
        if len(sizes) != 3:
            raise ValueError("Exactly three splitter sizes are required.")

        with self._connection:
            self._connection.execute(
                """
                INSERT INTO application_state (key, value)
                VALUES ('layout', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (
                    json.dumps(
                        {
                            "splitter_sizes": sizes,
                            "focused_department_id": focused_department_id,
                        }
                    ),
                ),
            )

    def load_layout(self) -> LayoutState | None:
        row = self._connection.execute(
            """
            SELECT value
            FROM application_state
            WHERE key = 'layout'
            """
        ).fetchone()

        if row is None:
            return None

        try:
            data = json.loads(row["value"])
            sizes = tuple(int(item) for item in data["splitter_sizes"])
            focused = data.get("focused_department_id")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

        if len(sizes) != 3:
            return None

        if focused not in (None, "project", "core", "research"):
            focused = None

        return LayoutState(
            splitter_sizes=(sizes[0], sizes[1], sizes[2]),
            focused_department_id=focused,
        )

    def replace_attachments(
        self,
        department_id: str,
        records: Iterable[AttachmentRecord],
    ) -> None:
        with self._connection:
            self._connection.execute(
                "DELETE FROM attachment WHERE department_id = ?",
                (department_id,),
            )
            self._connection.executemany(
                """
                INSERT INTO attachment (
                    department_id,
                    position,
                    path,
                    temporary
                )
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        department_id,
                        position,
                        str(record.path),
                        int(record.temporary),
                    )
                    for position, record in enumerate(records)
                ],
            )

    def load_attachments(
        self,
        department_id: str,
    ) -> tuple[AttachmentRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT path, temporary
            FROM attachment
            WHERE department_id = ?
            ORDER BY position
            """,
            (department_id,),
        ).fetchall()

        records: list[AttachmentRecord] = []
        for row in rows:
            path = Path(row["path"])
            if not path.is_file():
                continue
            records.append(
                AttachmentRecord(
                    path=path,
                    temporary=bool(row["temporary"]),
                )
            )
        return tuple(records)

    def _initialize_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS department_state (
                    department_id TEXT PRIMARY KEY,
                    conversation_text TEXT NOT NULL,
                    draft_text TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS application_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS attachment (
                    department_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    temporary INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (department_id, position)
                );

                CREATE TABLE IF NOT EXISTS department_chat_route (
                    department_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    project_url TEXT NOT NULL,
                    active_conversation_url TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS department_chat_history (
                    department_id TEXT NOT NULL,
                    conversation_url TEXT NOT NULL,
                    activated_at TEXT NOT NULL,
                    PRIMARY KEY (department_id, conversation_url)
                );
                """
            )
