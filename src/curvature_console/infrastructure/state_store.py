"""SQLite persistence for Curvature Console operational state."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from curvature_console.infrastructure.handoff import (
    HandoffMessage,
    HandoffRecord,
    HandoffStatus,
    validate_timeline,
)
from curvature_console.presentation.attachment_record import AttachmentRecord


@dataclass(frozen=True, slots=True)
class DepartmentState:
    """Persisted state for one department workspace."""

    conversation_text: str
    draft_text: str
    last_read_reply_count: int = 0


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
class GeneratedDownloadRecord:
    """Persisted generated file associated with one browser request."""

    request_id: str
    department_id: str
    conversation_url: str
    original_filename: str
    saved_path: Path
    source_url: str
    captured_at: str


@dataclass(frozen=True, slots=True)
class BrowserExchangeRecord:
    """Durable execution ledger entry for one Browser Bridge exchange."""

    request_id: str
    department_id: str
    exchange_type: str
    workflow_id: str | None
    state: str
    requested_conversation_url: str | None
    observed_conversation_url: str | None
    confirmation_marker: str | None
    queued_at: str
    started_at: str | None
    submitted_at: str | None
    response_received_at: str | None
    completed_at: str | None
    updated_at: str
    failure_reason: str | None
    cancel_submitted: bool | None
    recovery_disposition: str | None


@dataclass(frozen=True, slots=True)
class OperationalConversationRecord:
    """Persisted interdepartmental workflow conversation."""

    conversation_id: str
    source_request_id: str
    title: str
    participants: tuple[str, ...]
    status: str
    created_at: str
    updated_at: str
    result_ready_at: str | None
    closed_at: str | None
    round_count: int
    attention_kind: str | None
    attention_reason: str | None
    decision_domain: str | None
    decision_question: str | None
    decision_options: tuple[str, ...]
    decision_consequences: tuple[str, ...]
    decision_action_types: tuple[str, ...]
    blocked_request_body: str | None
    blocked_source_department_id: str | None
    blocked_target_department_id: str | None
    decision_status: str | None
    selected_option: str | None
    selected_action_type: str | None
    resolved_at: str | None


@dataclass(frozen=True, slots=True)
class OperationalConversationMessage:
    """One durable message in an operational conversation."""

    message_id: str
    conversation_id: str
    sequence: int
    author_department_id: str
    body: str
    created_at: str


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
        last_read_reply_count: int = 0,
    ) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO department_state (
                    department_id,
                    conversation_text,
                    draft_text,
                    last_read_reply_count
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(department_id) DO UPDATE SET
                    conversation_text = excluded.conversation_text,
                    draft_text = excluded.draft_text,
                    last_read_reply_count = excluded.last_read_reply_count
                """,
                (
                    department_id,
                    conversation_text,
                    draft_text,
                    max(0, int(last_read_reply_count)),
                ),
            )

    def load_department_state(
        self,
        department_id: str,
    ) -> DepartmentState | None:
        row = self._connection.execute(
            """
            SELECT conversation_text, draft_text, last_read_reply_count
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
            last_read_reply_count=row["last_read_reply_count"],
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


    def save_generated_downloads(
        self,
        request_id: str,
        department_id: str,
        conversation_url: str,
        downloads: Iterable[object],
    ) -> None:
        """Persist generated files captured for one completed response."""

        timestamp = datetime.now(UTC).isoformat()
        rows = []
        for position, download in enumerate(downloads):
            rows.append(
                (
                    request_id,
                    position,
                    department_id,
                    conversation_url,
                    str(download.original_filename),
                    str(Path(download.saved_path).expanduser()),
                    str(download.source_url),
                    timestamp,
                )
            )

        if not rows:
            return

        with self._connection:
            self._connection.executemany(
                """
                INSERT OR REPLACE INTO generated_download (
                    request_id,
                    position,
                    department_id,
                    conversation_url,
                    original_filename,
                    saved_path,
                    source_url,
                    captured_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def load_generated_downloads(
        self,
        department_id: str,
    ) -> tuple[GeneratedDownloadRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT
                request_id,
                department_id,
                conversation_url,
                original_filename,
                saved_path,
                source_url,
                captured_at
            FROM generated_download
            WHERE department_id = ?
            ORDER BY captured_at, request_id, position
            """,
            (department_id,),
        ).fetchall()

        return tuple(
            GeneratedDownloadRecord(
                request_id=row["request_id"],
                department_id=row["department_id"],
                conversation_url=row["conversation_url"],
                original_filename=row["original_filename"],
                saved_path=Path(row["saved_path"]),
                source_url=row["source_url"],
                captured_at=row["captured_at"],
            )
            for row in rows
        )

    def save_handoff(self, record: HandoffRecord) -> None:
        """Persist one complete handoff aggregate atomically."""

        validate_timeline(record.timeline)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO handoff_record (
                    handoff_id,
                    request_id,
                    source_department_id,
                    target_department_id,
                    status,
                    created_at,
                    updated_at,
                    user_visible_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(handoff_id) DO UPDATE SET
                    request_id = excluded.request_id,
                    source_department_id = excluded.source_department_id,
                    target_department_id = excluded.target_department_id,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    user_visible_message = excluded.user_visible_message
                """,
                (
                    record.handoff_id,
                    record.request_id,
                    record.source_department_id,
                    record.target_department_id,
                    record.status.value,
                    record.created_at,
                    record.updated_at,
                    record.user_visible_message,
                ),
            )
            self._connection.execute(
                "DELETE FROM handoff_message WHERE handoff_id = ?",
                (record.handoff_id,),
            )
            self._connection.executemany(
                """
                INSERT INTO handoff_message (
                    message_id,
                    handoff_id,
                    sequence,
                    author_department_id,
                    body,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        message.message_id,
                        message.handoff_id,
                        message.sequence,
                        message.author_department_id,
                        message.body,
                        message.created_at,
                    )
                    for message in record.timeline
                ],
            )

    def load_handoff(self, handoff_id: str) -> HandoffRecord | None:
        """Load one complete handoff aggregate."""

        row = self._connection.execute(
            """
            SELECT
                handoff_id,
                request_id,
                source_department_id,
                target_department_id,
                status,
                created_at,
                updated_at,
                user_visible_message
            FROM handoff_record
            WHERE handoff_id = ?
            """,
            (handoff_id,),
        ).fetchone()
        if row is None:
            return None

        return self._handoff_from_row(row)

    def load_handoffs(
        self,
        *,
        department_id: str | None = None,
        status: HandoffStatus | None = None,
    ) -> tuple[HandoffRecord, ...]:
        """Load handoffs with optional participant and status filters."""

        conditions: list[str] = []
        parameters: list[str] = []
        if department_id is not None:
            conditions.append(
                "(source_department_id = ? OR target_department_id = ?)"
            )
            parameters.extend((department_id, department_id))
        if status is not None:
            conditions.append("status = ?")
            parameters.append(status.value)

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        rows = self._connection.execute(
            """
            SELECT
                handoff_id,
                request_id,
                source_department_id,
                target_department_id,
                status,
                created_at,
                updated_at,
                user_visible_message
            FROM handoff_record
            """
            + where_clause
            + " ORDER BY created_at, handoff_id",
            tuple(parameters),
        ).fetchall()

        return tuple(self._handoff_from_row(row) for row in rows)

    def _handoff_from_row(self, row: sqlite3.Row) -> HandoffRecord:
        message_rows = self._connection.execute(
            """
            SELECT
                message_id,
                handoff_id,
                sequence,
                author_department_id,
                body,
                created_at
            FROM handoff_message
            WHERE handoff_id = ?
            ORDER BY sequence
            """,
            (row["handoff_id"],),
        ).fetchall()
        timeline = tuple(
            HandoffMessage(
                message_id=message_row["message_id"],
                handoff_id=message_row["handoff_id"],
                sequence=message_row["sequence"],
                author_department_id=message_row[
                    "author_department_id"
                ],
                body=message_row["body"],
                created_at=message_row["created_at"],
            )
            for message_row in message_rows
        )
        validate_timeline(timeline)
        return HandoffRecord(
            handoff_id=row["handoff_id"],
            request_id=row["request_id"],
            source_department_id=row["source_department_id"],
            target_department_id=row["target_department_id"],
            status=HandoffStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            user_visible_message=row["user_visible_message"],
            timeline=timeline,
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

    def create_operational_conversation(
        self,
        *,
        conversation_id: str,
        source_request_id: str,
        title: str,
        participants: Iterable[str],
        status: str = "RUNNING",
    ) -> None:
        """Create or refresh one durable interdepartmental conversation."""

        timestamp = datetime.now(UTC).isoformat()
        participant_json = json.dumps(tuple(participants))
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO operational_conversation (
                    conversation_id, source_request_id, title, participants_json,
                    status, created_at, updated_at, result_ready_at, closed_at,
                    round_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, 1)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    title = excluded.title,
                    participants_json = excluded.participants_json,
                    updated_at = excluded.updated_at
                """,
                (conversation_id, source_request_id, title, participant_json,
                 status, timestamp, timestamp),
            )

    def begin_operational_round(
        self, conversation_id: str, *, title: str | None = None
    ) -> int:
        """Resume an existing conversation as one additional logical round."""

        timestamp = datetime.now(UTC).isoformat()
        with self._connection:
            if title is None:
                self._connection.execute(
                    "UPDATE operational_conversation "
                    "SET status = 'RUNNING', updated_at = ?, "
                    "result_ready_at = NULL, closed_at = NULL, "
                    "attention_kind = NULL, attention_reason = NULL, "
                    "round_count = round_count + 1 "
                    "WHERE conversation_id = ?",
                    (timestamp, conversation_id),
                )
            else:
                self._connection.execute(
                    "UPDATE operational_conversation "
                    "SET title = ?, status = 'RUNNING', updated_at = ?, "
                    "result_ready_at = NULL, closed_at = NULL, "
                    "attention_kind = NULL, attention_reason = NULL, "
                    "round_count = round_count + 1 "
                    "WHERE conversation_id = ?",
                    (title, timestamp, conversation_id),
                )
            row = self._connection.execute(
                "SELECT round_count FROM operational_conversation "
                "WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(conversation_id)
        return int(row["round_count"])

    def append_operational_message(
        self,
        *,
        conversation_id: str,
        author_department_id: str,
        body: str,
    ) -> None:
        """Append one message while preserving deterministic sequence order."""

        timestamp = datetime.now(UTC).isoformat()
        with self._connection:
            row = self._connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence "
                "FROM operational_conversation_message "
                "WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            sequence = int(row["next_sequence"])
            self._connection.execute(
                """
                INSERT INTO operational_conversation_message (
                    message_id, conversation_id, sequence,
                    author_department_id, body, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"{conversation_id}:{sequence}", conversation_id, sequence,
                 author_department_id, body, timestamp),
            )
            self._connection.execute(
                "UPDATE operational_conversation SET updated_at = ? "
                "WHERE conversation_id = ?",
                (timestamp, conversation_id),
            )

    def update_operational_conversation_status(
        self, conversation_id: str, status: str
    ) -> None:
        timestamp = datetime.now(UTC).isoformat()
        result_statuses = {
            "RESULT_READY", "BLOCKED", "AWAITING_OPERATOR_DECISION"
        }
        closed_statuses = {"ACCEPTED", "REJECTED", "CANCELLED", "FAILED"}
        result_ready_at = timestamp if status in result_statuses else None
        closed_at = timestamp if status in closed_statuses else None
        with self._connection:
            self._connection.execute(
                "UPDATE operational_conversation "
                "SET status = ?, updated_at = ?, "
                "result_ready_at = COALESCE(?, result_ready_at), "
                "closed_at = COALESCE(?, closed_at) "
                "WHERE conversation_id = ?",
                (status, timestamp, result_ready_at, closed_at, conversation_id),
            )

    def update_operational_attention(
        self,
        conversation_id: str,
        *,
        attention_kind: str | None,
        attention_reason: str | None,
    ) -> None:
        """Persist why a completed conversation needs operator attention."""

        timestamp = datetime.now(UTC).isoformat()
        with self._connection:
            self._connection.execute(
                "UPDATE operational_conversation "
                "SET attention_kind = ?, attention_reason = ?, updated_at = ? "
                "WHERE conversation_id = ?",
                (attention_kind, attention_reason, timestamp, conversation_id),
            )


    def create_browser_exchange(
        self,
        *,
        request_id: str,
        department_id: str,
        exchange_type: str,
        workflow_id: str | None,
        requested_conversation_url: str | None,
        confirmation_marker: str | None,
    ) -> None:
        """Persist a queued Browser Bridge exchange before worker execution."""

        timestamp = datetime.now(UTC).isoformat()
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO browser_exchange (
                    request_id, department_id, exchange_type, workflow_id, state,
                    requested_conversation_url, confirmation_marker, queued_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, 'QUEUED', ?, ?, ?, ?)
                ON CONFLICT(request_id) DO NOTHING
                """,
                (
                    request_id, department_id, exchange_type, workflow_id,
                    requested_conversation_url, confirmation_marker, timestamp,
                    timestamp,
                ),
            )

    def update_browser_exchange_state(
        self,
        request_id: str,
        state: str,
        *,
        observed_conversation_url: str | None = None,
        failure_reason: str | None = None,
        cancel_submitted: bool | None = None,
    ) -> None:
        """Advance one durable Browser Bridge ledger entry."""

        timestamp = datetime.now(UTC).isoformat()
        started_at = timestamp if state != "QUEUED" else None
        submitted_at = (
            timestamp
            if state in {
                "SUBMITTED",
                "RESPONSE_RECEIVED",
                "COMPLETED",
                "ROUTE_UNVERIFIED",
            }
            or (state == "CANCELLED" and cancel_submitted is True)
            else None
        )
        response_received_at = (
            timestamp
            if state in {"RESPONSE_RECEIVED", "COMPLETED", "ROUTE_UNVERIFIED"}
            else None
        )
        completed_at = (
            timestamp
            if state in {"COMPLETED", "FAILED", "CANCELLED", "ROUTE_UNVERIFIED"}
            else None
        )
        cancel_value = None if cancel_submitted is None else int(cancel_submitted)
        with self._connection:
            self._connection.execute(
                """
                UPDATE browser_exchange
                SET state = ?,
                    observed_conversation_url = COALESCE(?, observed_conversation_url),
                    started_at = COALESCE(started_at, ?),
                    submitted_at = COALESCE(submitted_at, ?),
                    response_received_at = COALESCE(response_received_at, ?),
                    completed_at = COALESCE(completed_at, ?),
                    updated_at = ?,
                    failure_reason = COALESCE(?, failure_reason),
                    cancel_submitted = COALESCE(?, cancel_submitted)
                WHERE request_id = ?
                """,
                (
                    state, observed_conversation_url, started_at, submitted_at,
                    response_received_at, completed_at, timestamp, failure_reason,
                    cancel_value, request_id,
                ),
            )

    def load_browser_exchange(
        self, request_id: str
    ) -> BrowserExchangeRecord | None:
        row = self._connection.execute(
            "SELECT * FROM browser_exchange WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        return self._browser_exchange_record(row) if row is not None else None

    def load_browser_exchanges(self) -> tuple[BrowserExchangeRecord, ...]:
        rows = self._connection.execute(
            "SELECT * FROM browser_exchange ORDER BY queued_at, request_id"
        ).fetchall()
        return tuple(self._browser_exchange_record(row) for row in rows)

    @staticmethod
    def _browser_exchange_record(row: sqlite3.Row) -> BrowserExchangeRecord:
        cancel_submitted = row["cancel_submitted"]
        return BrowserExchangeRecord(
            request_id=row["request_id"],
            department_id=row["department_id"],
            exchange_type=row["exchange_type"],
            workflow_id=row["workflow_id"],
            state=row["state"],
            requested_conversation_url=row["requested_conversation_url"],
            observed_conversation_url=row["observed_conversation_url"],
            confirmation_marker=row["confirmation_marker"],
            queued_at=row["queued_at"],
            started_at=row["started_at"],
            submitted_at=row["submitted_at"],
            response_received_at=row["response_received_at"],
            completed_at=row["completed_at"],
            updated_at=row["updated_at"],
            failure_reason=row["failure_reason"],
            cancel_submitted=(
                None if cancel_submitted is None else bool(cancel_submitted)
            ),
            recovery_disposition=row["recovery_disposition"],
        )


    def save_operational_decision(
        self,
        conversation_id: str,
        *,
        domain: str,
        question: str,
        options: Iterable[str],
        consequences: Iterable[str],
        action_types: Iterable[str],
        blocked_request_body: str,
        source_department_id: str,
        target_department_id: str,
    ) -> None:
        """Persist the exact gated request needed for later operator resolution."""

        timestamp = datetime.now(UTC).isoformat()
        with self._connection:
            self._connection.execute(
                "UPDATE operational_conversation SET decision_domain = ?, "
                "decision_question = ?, decision_options_json = ?, "
                "decision_consequences_json = ?, decision_action_types_json = ?, "
                "blocked_request_body = ?, "
                "blocked_source_department_id = ?, "
                "blocked_target_department_id = ?, decision_status = 'PENDING', "
                "selected_option = NULL, selected_action_type = NULL, "
                "resolved_at = NULL, updated_at = ? "
                "WHERE conversation_id = ?",
                (
                    domain,
                    question,
                    json.dumps(tuple(options)),
                    json.dumps(tuple(consequences)),
                    json.dumps(tuple(action_types)),
                    blocked_request_body,
                    source_department_id,
                    target_department_id,
                    timestamp,
                    conversation_id,
                ),
            )

    def resolve_operational_decision(
        self,
        conversation_id: str,
        *,
        status: str,
        selected_option: str | None,
        selected_action_type: str | None = None,
    ) -> None:
        """Record one durable operator resolution for a gated request."""

        timestamp = datetime.now(UTC).isoformat()
        with self._connection:
            self._connection.execute(
                "UPDATE operational_conversation SET decision_status = ?, "
                "selected_option = ?, selected_action_type = ?, "
                "resolved_at = ?, updated_at = ? "
                "WHERE conversation_id = ?",
                (status, selected_option, selected_action_type, timestamp, timestamp, conversation_id),
            )



    def reconcile_interrupted_browser_exchanges(self) -> dict[str, int]:
        """Classify non-terminal Browser Bridge attempts conservatively after restart.

        Attempts with no evidence of submission become RETRY_PENDING. Attempts that
        may already have crossed the submission boundary become RECONCILE_REQUIRED.
        No resend is performed here.
        """

        timestamp = datetime.now(UTC).isoformat()
        safe_reason = (
            "Console restart interrupted this Browser Bridge exchange before any "
            "durable evidence of submission. A controlled retry is permitted; no "
            "automatic resend was performed."
        )
        reconcile_reason = (
            "Console restart interrupted this Browser Bridge exchange after the "
            "submission boundary may have been crossed. Reconcile the existing "
            "ChatGPT conversation before any retry; blind resend is prohibited."
        )
        with self._connection:
            retry_cursor = self._connection.execute(
                "UPDATE browser_exchange "
                "SET state = 'RETRY_PENDING', recovery_disposition = 'SAFE_RETRY', "
                "updated_at = ?, failure_reason = COALESCE(failure_reason, ?) "
                "WHERE state IN ('QUEUED', 'STARTED') AND submitted_at IS NULL",
                (timestamp, safe_reason),
            )
            reconcile_cursor = self._connection.execute(
                "UPDATE browser_exchange "
                "SET state = 'RECONCILE_REQUIRED', "
                "recovery_disposition = 'RECONCILE_BEFORE_RETRY', "
                "updated_at = ?, failure_reason = COALESCE(failure_reason, ?) "
                "WHERE (state IN ('SUBMITTED', 'RESPONSE_RECEIVED') "
                "OR (state IN ('QUEUED', 'STARTED') AND submitted_at IS NOT NULL))",
                (timestamp, reconcile_reason),
            )
        return {
            "retry_pending": int(retry_cursor.rowcount),
            "reconcile_required": int(reconcile_cursor.rowcount),
        }

    def recover_interrupted_handoffs(self) -> int:
        """Move process-bound supervised handoff transports to HELD after restart."""

        recovered = 0
        recovery_reason = (
            "Console restart interrupted an in-process Browser Bridge transport. "
            "The handoff was held for operator review before any retry."
        )
        for status in (
            HandoffStatus.SENT,
            HandoffStatus.RETURN_SENT,
            HandoffStatus.UPDATE_SENT,
        ):
            for record in self.load_handoffs(status=status):
                if status is HandoffStatus.RETURN_SENT:
                    author_department_id = record.target_department_id
                    prefix = "Controlled return interrupted and held: "
                elif status is HandoffStatus.UPDATE_SENT:
                    author_department_id = record.source_department_id
                    prefix = "Progress update interrupted and held: "
                else:
                    author_department_id = record.source_department_id
                    prefix = "Controlled delivery interrupted and held: "
                held = record.transition(HandoffStatus.HELD).append_message(
                    author_department_id,
                    prefix + recovery_reason,
                )
                self.save_handoff(held)
                recovered += 1
        return recovered

    def recover_interrupted_operational_conversations(self) -> int:
        """Mark process-bound operational work as interrupted after restart."""

        timestamp = datetime.now(UTC).isoformat()
        reason = (
            "The Console restarted while this operational conversation was active "
            "or waiting for an in-process department return. No active worker can "
            "still own it; operator review is required before retry."
        )
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE operational_conversation "
                "SET status = 'BLOCKED', updated_at = ?, "
                "result_ready_at = COALESCE(result_ready_at, ?), "
                "attention_kind = 'BLOCKER', attention_reason = ? "
                "WHERE status IN ('RUNNING', 'WAITING_SOURCE')",
                (timestamp, timestamp, reason),
            )
        return int(cursor.rowcount)

    def count_operational_attention(self) -> dict[str, int]:
        """Return review counts grouped by operator-attention classification."""

        rows = self._connection.execute(
            "SELECT COALESCE(attention_kind, 'RESULT') AS kind, COUNT(*) AS count "
            "FROM operational_conversation "
            "WHERE status IN ('RESULT_READY', 'BLOCKED', "
            "'AWAITING_OPERATOR_DECISION') "
            "AND (decision_status IS NULL OR decision_status = 'PENDING') "
            "GROUP BY kind"
        ).fetchall()
        return {str(row["kind"]): int(row["count"]) for row in rows}

    def load_operational_conversation(
        self, conversation_id: str
    ) -> OperationalConversationRecord | None:
        row = self._connection.execute(
            "SELECT * FROM operational_conversation WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()
        return self._operational_record(row) if row is not None else None

    def load_operational_conversations(
        self,
    ) -> tuple[OperationalConversationRecord, ...]:
        rows = self._connection.execute(
            "SELECT * FROM operational_conversation ORDER BY updated_at DESC"
        ).fetchall()
        return tuple(self._operational_record(row) for row in rows)

    def load_operational_messages(
        self, conversation_id: str
    ) -> tuple[OperationalConversationMessage, ...]:
        rows = self._connection.execute(
            "SELECT * FROM operational_conversation_message "
            "WHERE conversation_id = ? ORDER BY sequence",
            (conversation_id,),
        ).fetchall()
        return tuple(
            OperationalConversationMessage(
                message_id=row["message_id"],
                conversation_id=row["conversation_id"],
                sequence=row["sequence"],
                author_department_id=row["author_department_id"],
                body=row["body"],
                created_at=row["created_at"],
            )
            for row in rows
        )

    def count_operational_reviews(self) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM operational_conversation "
            "WHERE status IN ('RESULT_READY', 'BLOCKED', "
            "'AWAITING_OPERATOR_DECISION') "
            "AND (decision_status IS NULL OR decision_status = 'PENDING')"
        ).fetchone()
        return int(row["count"])

    @staticmethod
    def _operational_record(row: sqlite3.Row) -> OperationalConversationRecord:
        return OperationalConversationRecord(
            conversation_id=row["conversation_id"],
            source_request_id=row["source_request_id"],
            title=row["title"],
            participants=tuple(json.loads(row["participants_json"])),
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            result_ready_at=row["result_ready_at"],
            closed_at=row["closed_at"],
            round_count=int(row["round_count"]),
            attention_kind=row["attention_kind"],
            attention_reason=row["attention_reason"],
            decision_domain=row["decision_domain"],
            decision_question=row["decision_question"],
            decision_options=tuple(json.loads(row["decision_options_json"] or "[]")),
            decision_consequences=tuple(json.loads(row["decision_consequences_json"] or "[]")),
            decision_action_types=tuple(json.loads(row["decision_action_types_json"] or "[]")),
            blocked_request_body=row["blocked_request_body"],
            blocked_source_department_id=row["blocked_source_department_id"],
            blocked_target_department_id=row["blocked_target_department_id"],
            decision_status=row["decision_status"],
            selected_option=row["selected_option"],
            selected_action_type=row["selected_action_type"],
            resolved_at=row["resolved_at"],
        )

    def _initialize_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS department_state (
                    department_id TEXT PRIMARY KEY,
                    conversation_text TEXT NOT NULL,
                    draft_text TEXT NOT NULL,
                    last_read_reply_count INTEGER NOT NULL DEFAULT 0
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

                CREATE TABLE IF NOT EXISTS generated_download (
                    request_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    department_id TEXT NOT NULL,
                    conversation_url TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    saved_path TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    PRIMARY KEY (request_id, position)
                );

                CREATE INDEX IF NOT EXISTS idx_generated_download_department
                ON generated_download (department_id, captured_at);

                CREATE TABLE IF NOT EXISTS browser_exchange (
                    request_id TEXT PRIMARY KEY,
                    department_id TEXT NOT NULL,
                    exchange_type TEXT NOT NULL,
                    workflow_id TEXT,
                    state TEXT NOT NULL,
                    requested_conversation_url TEXT,
                    observed_conversation_url TEXT,
                    confirmation_marker TEXT,
                    queued_at TEXT NOT NULL,
                    started_at TEXT,
                    submitted_at TEXT,
                    response_received_at TEXT,
                    completed_at TEXT,
                    updated_at TEXT NOT NULL,
                    failure_reason TEXT,
                    cancel_submitted INTEGER,
                    recovery_disposition TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_browser_exchange_state
                ON browser_exchange (state, updated_at);

                CREATE INDEX IF NOT EXISTS idx_browser_exchange_workflow
                ON browser_exchange (workflow_id, updated_at);

                CREATE TABLE IF NOT EXISTS handoff_record (
                    handoff_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    source_department_id TEXT NOT NULL,
                    target_department_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    user_visible_message TEXT NOT NULL,
                    CHECK (
                        source_department_id
                        IN ('project', 'core', 'research')
                    ),
                    CHECK (
                        target_department_id
                        IN ('project', 'core', 'research')
                    ),
                    CHECK (
                        source_department_id != target_department_id
                    ),
                    CHECK (
                        status IN (
                            'draft',
                            'pending_approval',
                            'approved',
                            'sent',
                            'received',
                            'answered',
                            'awaiting_user_decision',
                            'in_progress',
                            'update_sent',
                            'return_sent',
                            'returned',
                            'closed',
                            'rejected',
                            'held',
                            'stopped'
                        )
                    )
                );

                CREATE INDEX IF NOT EXISTS idx_handoff_source
                ON handoff_record (source_department_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_handoff_target
                ON handoff_record (target_department_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_handoff_status
                ON handoff_record (status, updated_at);

                CREATE TABLE IF NOT EXISTS handoff_message (
                    message_id TEXT PRIMARY KEY,
                    handoff_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    author_department_id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (handoff_id, sequence),
                    FOREIGN KEY (handoff_id)
                        REFERENCES handoff_record(handoff_id)
                        ON DELETE CASCADE,
                    CHECK (
                        author_department_id
                        IN ('project', 'core', 'research')
                    )
                );

                CREATE TABLE IF NOT EXISTS operational_conversation (
                    conversation_id TEXT PRIMARY KEY,
                    source_request_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    participants_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result_ready_at TEXT,
                    closed_at TEXT,
                    round_count INTEGER NOT NULL DEFAULT 1,
                    attention_kind TEXT,
                    attention_reason TEXT,
                    decision_domain TEXT,
                    decision_question TEXT,
                    decision_options_json TEXT,
                    decision_consequences_json TEXT,
                    decision_action_types_json TEXT,
                    blocked_request_body TEXT,
                    blocked_source_department_id TEXT,
                    blocked_target_department_id TEXT,
                    decision_status TEXT,
                    selected_option TEXT,
                    selected_action_type TEXT,
                    resolved_at TEXT
                );

                CREATE TABLE IF NOT EXISTS operational_conversation_message (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    author_department_id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (conversation_id, sequence),
                    FOREIGN KEY (conversation_id)
                        REFERENCES operational_conversation(conversation_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_operational_conversation_status
                ON operational_conversation (status, updated_at);

                CREATE TABLE IF NOT EXISTS department_chat_history (
                    department_id TEXT NOT NULL,
                    conversation_url TEXT NOT NULL,
                    activated_at TEXT NOT NULL,
                    PRIMARY KEY (department_id, conversation_url)
                );
                """
            )

        self._migrate_department_reply_state()
        self._migrate_handoff_status_constraint()
        self._migrate_operational_conversation_lifecycle()
        self._migrate_browser_exchange_recovery()



    def _migrate_browser_exchange_recovery(self) -> None:
        """Add restart-reconciliation metadata to pre-B7C databases."""

        columns = {
            row["name"]
            for row in self._connection.execute(
                "PRAGMA table_info(browser_exchange)"
            ).fetchall()
        }
        if "recovery_disposition" in columns:
            return
        with self._connection:
            self._connection.execute(
                "ALTER TABLE browser_exchange ADD COLUMN recovery_disposition TEXT"
            )

    def _migrate_operational_conversation_lifecycle(self) -> None:
        """Add lifecycle columns to databases created before CDU-004B2A."""

        columns = {
            row["name"]
            for row in self._connection.execute(
                "PRAGMA table_info(operational_conversation)"
            ).fetchall()
        }
        additions = (
            ("result_ready_at", "TEXT"),
            ("closed_at", "TEXT"),
            ("round_count", "INTEGER NOT NULL DEFAULT 1"),
            ("attention_kind", "TEXT"),
            ("attention_reason", "TEXT"),
            ("decision_domain", "TEXT"),
            ("decision_question", "TEXT"),
            ("decision_options_json", "TEXT"),
            ("decision_consequences_json", "TEXT"),
            ("decision_action_types_json", "TEXT"),
            ("blocked_request_body", "TEXT"),
            ("blocked_source_department_id", "TEXT"),
            ("blocked_target_department_id", "TEXT"),
            ("decision_status", "TEXT"),
            ("selected_option", "TEXT"),
            ("selected_action_type", "TEXT"),
            ("resolved_at", "TEXT"),
        )
        with self._connection:
            for name, declaration in additions:
                if name not in columns:
                    self._connection.execute(
                        f"ALTER TABLE operational_conversation ADD COLUMN {name} {declaration}"
                    )

    def _migrate_department_reply_state(self) -> None:
        """Add persisted reply-read state to databases created by older builds."""

        columns = {
            row["name"]
            for row in self._connection.execute(
                "PRAGMA table_info(department_state)"
            ).fetchall()
        }
        if "last_read_reply_count" in columns:
            return
        with self._connection:
            self._connection.execute(
                "ALTER TABLE department_state "
                "ADD COLUMN last_read_reply_count INTEGER NOT NULL DEFAULT 0"
            )

    def _migrate_handoff_status_constraint(self) -> None:
        """Expand legacy handoff status CHECK constraints without data loss."""

        row = self._connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = 'handoff_record'
            """
        ).fetchone()
        schema_sql = "" if row is None or row["sql"] is None else row["sql"]
        required_statuses = (
            "awaiting_user_decision",
            "in_progress",
            "update_sent",
            "return_sent",
            "returned",
        )
        if all(status in schema_sql for status in required_statuses):
            return

        self._connection.commit()
        self._connection.execute("PRAGMA foreign_keys = OFF")
        try:
            with self._connection:
                self._connection.executescript(
                    """
                    DROP TABLE IF EXISTS handoff_record_new;

                    CREATE TABLE handoff_record_new (
                        handoff_id TEXT PRIMARY KEY,
                        request_id TEXT NOT NULL,
                        source_department_id TEXT NOT NULL,
                        target_department_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        user_visible_message TEXT NOT NULL,
                        CHECK (
                            source_department_id
                            IN ('project', 'core', 'research')
                        ),
                        CHECK (
                            target_department_id
                            IN ('project', 'core', 'research')
                        ),
                        CHECK (
                            source_department_id != target_department_id
                        ),
                        CHECK (
                            status IN (
                                'draft',
                                'pending_approval',
                                'approved',
                                'sent',
                                'received',
                                'answered',
                                'awaiting_user_decision',
                                'in_progress',
                                'update_sent',
                                'return_sent',
                                'returned',
                                'closed',
                                'rejected',
                                'held',
                                'stopped'
                            )
                        )
                    );

                    INSERT INTO handoff_record_new (
                        handoff_id,
                        request_id,
                        source_department_id,
                        target_department_id,
                        status,
                        created_at,
                        updated_at,
                        user_visible_message
                    )
                    SELECT
                        handoff_id,
                        request_id,
                        source_department_id,
                        target_department_id,
                        status,
                        created_at,
                        updated_at,
                        user_visible_message
                    FROM handoff_record;

                    DROP TABLE handoff_record;
                    ALTER TABLE handoff_record_new RENAME TO handoff_record;

                    CREATE INDEX IF NOT EXISTS idx_handoff_source
                    ON handoff_record (source_department_id, created_at);

                    CREATE INDEX IF NOT EXISTS idx_handoff_target
                    ON handoff_record (target_department_id, created_at);

                    CREATE INDEX IF NOT EXISTS idx_handoff_status
                    ON handoff_record (status, updated_at);
                    """
                )
        finally:
            self._connection.execute("PRAGMA foreign_keys = ON")
