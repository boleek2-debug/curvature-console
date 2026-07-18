"""SQLite persistence for Curvature Console operational state."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
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
        """Close the SQLite connection."""

        self._connection.close()

    def save_department_state(
        self,
        department_id: str,
        conversation_text: str,
        draft_text: str,
    ) -> None:
        """Insert or update one department state."""

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
        """Load one department state."""

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

    def save_layout(
        self,
        splitter_sizes: Iterable[int],
        focused_department_id: str | None,
    ) -> None:
        """Persist splitter widths and focus state."""

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
        """Load splitter widths and focus state."""

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
        """Replace persisted attachment metadata for one department."""

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
        """Load existing attachment paths for one department."""

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
                """
            )
