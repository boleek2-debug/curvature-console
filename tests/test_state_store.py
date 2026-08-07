"""Tests for SQLite operational state persistence."""

from __future__ import annotations

from pathlib import Path

from curvature_console.infrastructure.state_store import SQLiteStateStore
from curvature_console.presentation.attachment_record import AttachmentRecord


def test_department_state_survives_reopen(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"

    store = SQLiteStateStore(database)
    store.save_department_state(
        "core",
        "Core transcript",
        "Unsaved Core draft",
        last_read_reply_count=3,
    )
    store.close()

    reopened = SQLiteStateStore(database)
    state = reopened.load_department_state("core")

    assert state is not None
    assert state.conversation_text == "Core transcript"
    assert state.draft_text == "Unsaved Core draft"
    assert state.last_read_reply_count == 3

    reopened.close()


def test_layout_survives_reopen(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"

    store = SQLiteStateStore(database)
    store.save_layout([320, 640, 480], "research")
    store.close()

    reopened = SQLiteStateStore(database)
    layout = reopened.load_layout()

    assert layout is not None
    assert layout.splitter_sizes == (320, 640, 480)
    assert layout.focused_department_id == "research"

    reopened.close()


def test_attachment_metadata_survives_reopen(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    attachment = tmp_path / "paper.pdf"
    attachment.write_bytes(b"%PDF-test")

    store = SQLiteStateStore(database)
    store.replace_attachments(
        "research",
        [AttachmentRecord(path=attachment)],
    )
    store.close()

    reopened = SQLiteStateStore(database)
    records = reopened.load_attachments("research")

    assert len(records) == 1
    assert records[0].path == attachment
    assert records[0].name == "paper.pdf"

    reopened.close()


def test_missing_attachment_is_not_restored(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    attachment = tmp_path / "temporary.txt"
    attachment.write_text("temporary", encoding="utf-8")

    store = SQLiteStateStore(database)
    store.replace_attachments(
        "project",
        [AttachmentRecord(path=attachment)],
    )
    store.close()

    attachment.unlink()

    reopened = SQLiteStateStore(database)

    assert reopened.load_attachments("project") == ()

    reopened.close()


def test_chat_route_and_history_survive_reopen(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"

    store = SQLiteStateStore(database)
    store.save_chat_route(
        "core",
        "Curvature Core",
        "https://chatgpt.com/g/g-p-core/project",
        "https://chatgpt.com/c/first-core-chat",
    )
    store.save_chat_route(
        "core",
        "Curvature Core",
        "https://chatgpt.com/g/g-p-core/project",
        "https://chatgpt.com/c/second-core-chat",
    )
    store.close()

    reopened = SQLiteStateStore(database)
    route = reopened.load_chat_route("core")
    history = reopened.load_chat_history("core")

    assert route is not None
    assert route.project_name == "Curvature Core"
    assert route.project_url == "https://chatgpt.com/g/g-p-core/project"
    assert (
        route.active_conversation_url
        == "https://chatgpt.com/c/second-core-chat"
    )
    assert [entry.conversation_url for entry in history] == [
        "https://chatgpt.com/c/first-core-chat",
        "https://chatgpt.com/c/second-core-chat",
    ]

    reopened.close()


def test_generated_download_metadata_survives_reopen(
    tmp_path: Path,
) -> None:
    from curvature_console.infrastructure.browser_bridge import CapturedDownload

    database = tmp_path / "state.sqlite3"
    saved = tmp_path / "download-inbox" / "package.zip"
    saved.parent.mkdir()
    saved.write_bytes(b"zip")

    store = SQLiteStateStore(database)
    store.save_generated_downloads(
        request_id="request-123",
        department_id="core",
        conversation_url="https://chatgpt.com/c/core-id",
        downloads=(
            CapturedDownload(
                original_filename="package.zip",
                saved_path=saved,
                source_url="sandbox:/mnt/data/package.zip",
            ),
        ),
    )
    store.close()

    reopened = SQLiteStateStore(database)
    records = reopened.load_generated_downloads("core")

    assert len(records) == 1
    assert records[0].request_id == "request-123"
    assert records[0].original_filename == "package.zip"
    assert records[0].saved_path == saved
    assert records[0].conversation_url == "https://chatgpt.com/c/core-id"

    reopened.close()



def test_handoff_and_full_timeline_survive_reopen(tmp_path: Path) -> None:
    from curvature_console.infrastructure.handoff import (
        HandoffStatus,
        create_handoff,
    )

    database = tmp_path / "state.sqlite3"
    handoff = create_handoff(
        handoff_id="handoff-1",
        request_id="request-1",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Implement the approved model.",
        created_at="2026-07-29T12:00:00+00:00",
    )
    handoff = handoff.append_message(
        "project",
        "Start with persistence and tests.",
        message_id="message-1",
        created_at="2026-07-29T12:01:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.PENDING_APPROVAL,
        updated_at="2026-07-29T12:02:00+00:00",
    )

    store = SQLiteStateStore(database)
    store.save_handoff(handoff)
    store.close()

    reopened = SQLiteStateStore(database)
    restored = reopened.load_handoff("handoff-1")

    assert restored == handoff
    assert restored is not None
    assert restored.timeline[0].body == "Start with persistence and tests."
    reopened.close()


def test_handoff_filters_include_source_and_target_departments(
    tmp_path: Path,
) -> None:
    from curvature_console.infrastructure.handoff import (
        HandoffStatus,
        create_handoff,
    )

    database = tmp_path / "state.sqlite3"
    project_to_core = create_handoff(
        handoff_id="handoff-1",
        request_id="request-1",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Implement this.",
        created_at="2026-07-29T12:00:00+00:00",
    ).transition(
        HandoffStatus.PENDING_APPROVAL,
        updated_at="2026-07-29T12:01:00+00:00",
    )
    research_to_project = create_handoff(
        handoff_id="handoff-2",
        request_id="request-2",
        source_department_id="research",
        target_department_id="project",
        user_visible_message="Review this.",
        created_at="2026-07-29T12:02:00+00:00",
    )

    store = SQLiteStateStore(database)
    store.save_handoff(project_to_core)
    store.save_handoff(research_to_project)

    project_records = store.load_handoffs(department_id="project")
    pending_records = store.load_handoffs(
        status=HandoffStatus.PENDING_APPROVAL
    )

    assert [item.handoff_id for item in project_records] == [
        "handoff-1",
        "handoff-2",
    ]
    assert [item.handoff_id for item in pending_records] == ["handoff-1"]
    store.close()


def test_saving_updated_handoff_replaces_timeline_atomically(
    tmp_path: Path,
) -> None:
    from curvature_console.infrastructure.handoff import create_handoff

    database = tmp_path / "state.sqlite3"
    handoff = create_handoff(
        handoff_id="handoff-1",
        request_id="request-1",
        source_department_id="core",
        target_department_id="research",
        user_visible_message="Confirm this.",
    )

    store = SQLiteStateStore(database)
    store.save_handoff(handoff)
    updated = handoff.append_message(
        "research",
        "Confirmed.",
        message_id="message-1",
    )
    store.save_handoff(updated)

    restored = store.load_handoff("handoff-1")

    assert restored is not None
    assert restored.timeline == updated.timeline
    store.close()


def test_legacy_handoff_status_constraint_is_migrated_without_data_loss(
    tmp_path: Path,
) -> None:
    import sqlite3

    database = tmp_path / "state.sqlite3"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE handoff_record (
            handoff_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            source_department_id TEXT NOT NULL,
            target_department_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            user_visible_message TEXT NOT NULL,
            CHECK (
                source_department_id IN ('project', 'core', 'research')
            ),
            CHECK (
                target_department_id IN ('project', 'core', 'research')
            ),
            CHECK (source_department_id != target_department_id),
            CHECK (
                status IN (
                    'draft',
                    'pending_approval',
                    'approved',
                    'sent',
                    'received',
                    'answered',
                    'closed',
                    'rejected',
                    'held',
                    'stopped'
                )
            )
        );

        CREATE TABLE handoff_message (
            message_id TEXT PRIMARY KEY,
            handoff_id TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            author_department_id TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE (handoff_id, sequence),
            FOREIGN KEY (handoff_id)
                REFERENCES handoff_record(handoff_id)
                ON DELETE CASCADE
        );

        INSERT INTO handoff_record (
            handoff_id,
            request_id,
            source_department_id,
            target_department_id,
            status,
            created_at,
            updated_at,
            user_visible_message
        ) VALUES (
            'handoff-legacy',
            'request-legacy',
            'project',
            'core',
            'answered',
            '2026-07-30T10:00:00+00:00',
            '2026-07-30T10:01:00+00:00',
            'Legacy handoff'
        );

        INSERT INTO handoff_message (
            message_id,
            handoff_id,
            sequence,
            author_department_id,
            body,
            created_at
        ) VALUES (
            'message-legacy',
            'handoff-legacy',
            0,
            'core',
            'Legacy reply',
            '2026-07-30T10:01:00+00:00'
        );
        """
    )
    connection.close()

    store = SQLiteStateStore(database)
    restored = store.load_handoff("handoff-legacy")

    assert restored is not None
    assert restored.status.value == "answered"
    assert restored.timeline[0].body == "Legacy reply"

    from dataclasses import replace
    from curvature_console.infrastructure.handoff import HandoffStatus

    updated = replace(
        restored,
        status=HandoffStatus.AWAITING_USER_DECISION,
    )
    store.save_handoff(updated)
    store.close()

    reopened = SQLiteStateStore(database)
    migrated = reopened.load_handoff("handoff-legacy")

    assert migrated is not None
    assert migrated.status.value == "awaiting_user_decision"
    assert migrated.timeline[0].body == "Legacy reply"
    reopened.close()


def test_legacy_department_state_gains_reply_read_column(tmp_path: Path) -> None:
    import sqlite3

    database = tmp_path / "legacy-state.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE department_state ("
        "department_id TEXT PRIMARY KEY, "
        "conversation_text TEXT NOT NULL, "
        "draft_text TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT INTO department_state VALUES (?, ?, ?)",
        ("project", "Transcript", "Draft"),
    )
    connection.commit()
    connection.close()

    store = SQLiteStateStore(database)
    state = store.load_department_state("project")
    assert state is not None
    assert state.last_read_reply_count == 0
    store.save_department_state(
        "project", "Transcript", "Draft", last_read_reply_count=2
    )
    assert store.load_department_state("project").last_read_reply_count == 2
    store.close()


def test_update_sent_handoff_status_persists(tmp_path) -> None:
    from curvature_console.infrastructure.handoff import HandoffStatus, create_handoff

    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    record = create_handoff(
        handoff_id="handoff-update-status",
        request_id="request-update-status",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Continue this handoff.",
    )
    for status in (
        HandoffStatus.PENDING_APPROVAL,
        HandoffStatus.APPROVED,
        HandoffStatus.SENT,
        HandoffStatus.RECEIVED,
        HandoffStatus.AWAITING_USER_DECISION,
        HandoffStatus.IN_PROGRESS,
        HandoffStatus.UPDATE_SENT,
    ):
        record = record.transition(status)
    store.save_handoff(record)

    restored = store.load_handoff(record.handoff_id)

    assert restored is not None
    assert restored.status is HandoffStatus.UPDATE_SENT
    store.close()


def test_browser_exchange_ledger_survives_reopen_and_records_lifecycle(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state.sqlite3"

    store = SQLiteStateStore(database)
    store.create_browser_exchange(
        request_id="exchange-1",
        department_id="core",
        exchange_type="OPERATIONAL_REQUEST",
        workflow_id="operational-chain-1",
        requested_conversation_url="https://chatgpt.com/c/core",
        confirmation_marker="CURVATURE_REQUEST_ID: exchange-1",
    )
    store.update_browser_exchange_state("exchange-1", "STARTED")
    store.update_browser_exchange_state("exchange-1", "SUBMITTED")
    store.update_browser_exchange_state("exchange-1", "RESPONSE_RECEIVED")
    store.update_browser_exchange_state(
        "exchange-1",
        "COMPLETED",
        observed_conversation_url="https://chatgpt.com/c/core",
    )
    store.close()

    reopened = SQLiteStateStore(database)
    record = reopened.load_browser_exchange("exchange-1")

    assert record is not None
    assert record.department_id == "core"
    assert record.exchange_type == "OPERATIONAL_REQUEST"
    assert record.workflow_id == "operational-chain-1"
    assert record.state == "COMPLETED"
    assert record.queued_at
    assert record.started_at
    assert record.submitted_at
    assert record.response_received_at
    assert record.completed_at
    assert record.requested_conversation_url == "https://chatgpt.com/c/core"
    assert record.observed_conversation_url == "https://chatgpt.com/c/core"
    assert record.confirmation_marker == "CURVATURE_REQUEST_ID: exchange-1"
    assert record.failure_reason is None
    assert record.cancel_submitted is None
    reopened.close()


def test_browser_exchange_ledger_records_cancel_submission_boundary(
    tmp_path: Path,
) -> None:
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    store.create_browser_exchange(
        request_id="exchange-cancelled",
        department_id="project",
        exchange_type="DEPARTMENT_CHAT",
        workflow_id=None,
        requested_conversation_url="https://chatgpt.com/c/project",
        confirmation_marker=None,
    )
    store.update_browser_exchange_state("exchange-cancelled", "STARTED")
    store.update_browser_exchange_state(
        "exchange-cancelled",
        "CANCELLED",
        failure_reason="Cancelled by operator before submission.",
        cancel_submitted=False,
    )

    record = store.load_browser_exchange("exchange-cancelled")

    assert record is not None
    assert record.state == "CANCELLED"
    assert record.started_at
    assert record.submitted_at is None
    assert record.completed_at
    assert record.cancel_submitted is False
    assert record.failure_reason == "Cancelled by operator before submission."
    store.close()


def test_interrupted_supervised_handoff_transports_recover_to_held(tmp_path: Path) -> None:
    from curvature_console.infrastructure.handoff import HandoffStatus, create_handoff

    store = SQLiteStateStore(tmp_path / "state.sqlite3")

    sent = create_handoff(
        handoff_id="handoff-sent-recovery",
        request_id="request-sent-recovery",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Deliver this.",
    )
    for status in (
        HandoffStatus.PENDING_APPROVAL,
        HandoffStatus.APPROVED,
        HandoffStatus.SENT,
    ):
        sent = sent.transition(status)
    store.save_handoff(sent)

    returning = create_handoff(
        handoff_id="handoff-return-recovery",
        request_id="request-return-recovery",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Return this.",
    )
    for status in (
        HandoffStatus.PENDING_APPROVAL,
        HandoffStatus.APPROVED,
        HandoffStatus.SENT,
        HandoffStatus.RECEIVED,
        HandoffStatus.ANSWERED,
        HandoffStatus.RETURN_SENT,
    ):
        returning = returning.transition(status)
    store.save_handoff(returning)

    updating = create_handoff(
        handoff_id="handoff-update-recovery",
        request_id="request-update-recovery",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Update this.",
    )
    for status in (
        HandoffStatus.PENDING_APPROVAL,
        HandoffStatus.APPROVED,
        HandoffStatus.SENT,
        HandoffStatus.RECEIVED,
        HandoffStatus.AWAITING_USER_DECISION,
        HandoffStatus.IN_PROGRESS,
        HandoffStatus.UPDATE_SENT,
    ):
        updating = updating.transition(status)
    store.save_handoff(updating)

    assert store.recover_interrupted_handoffs() == 3

    for handoff_id in (
        "handoff-sent-recovery",
        "handoff-return-recovery",
        "handoff-update-recovery",
    ):
        record = store.load_handoff(handoff_id)
        assert record is not None
        assert record.status is HandoffStatus.HELD
        assert "interrupted" in record.timeline[-1].body.casefold()

    assert store.recover_interrupted_handoffs() == 0
    store.close()


def test_browser_exchange_restart_reconciliation_separates_safe_retry_from_possible_submission(
    tmp_path: Path,
) -> None:
    store = SQLiteStateStore(tmp_path / "state.sqlite3")

    for request_id, state in (
        ("queued-safe", "QUEUED"),
        ("started-safe", "STARTED"),
        ("submitted-unsafe", "SUBMITTED"),
        ("response-unsafe", "RESPONSE_RECEIVED"),
        ("completed-terminal", "COMPLETED"),
    ):
        store.create_browser_exchange(
            request_id=request_id,
            department_id="core",
            exchange_type="OPERATIONAL_REQUEST",
            workflow_id="operational-chain-recovery",
            requested_conversation_url="https://chatgpt.com/c/core",
            confirmation_marker=f"CURVATURE_REQUEST_ID: {request_id}",
        )
        if state != "QUEUED":
            store.update_browser_exchange_state(request_id, state)

    counts = store.reconcile_interrupted_browser_exchanges()

    assert counts == {"retry_pending": 2, "reconcile_required": 2}

    queued = store.load_browser_exchange("queued-safe")
    started = store.load_browser_exchange("started-safe")
    submitted = store.load_browser_exchange("submitted-unsafe")
    response = store.load_browser_exchange("response-unsafe")
    completed = store.load_browser_exchange("completed-terminal")

    assert queued is not None and queued.state == "RETRY_PENDING"
    assert queued.recovery_disposition == "SAFE_RETRY"
    assert started is not None and started.state == "RETRY_PENDING"
    assert started.recovery_disposition == "SAFE_RETRY"
    assert submitted is not None and submitted.state == "RECONCILE_REQUIRED"
    assert submitted.recovery_disposition == "RECONCILE_BEFORE_RETRY"
    assert response is not None and response.state == "RECONCILE_REQUIRED"
    assert response.recovery_disposition == "RECONCILE_BEFORE_RETRY"
    assert completed is not None and completed.state == "COMPLETED"
    assert completed.recovery_disposition is None
    store.close()


def test_browser_exchange_restart_reconciliation_is_idempotent(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    store.create_browser_exchange(
        request_id="queued-once",
        department_id="project",
        exchange_type="DEPARTMENT_CHAT",
        workflow_id=None,
        requested_conversation_url="https://chatgpt.com/c/project",
        confirmation_marker=None,
    )

    first = store.reconcile_interrupted_browser_exchanges()
    second = store.reconcile_interrupted_browser_exchanges()
    record = store.load_browser_exchange("queued-once")

    assert first == {"retry_pending": 1, "reconcile_required": 0}
    assert second == {"retry_pending": 0, "reconcile_required": 0}
    assert record is not None
    assert record.state == "RETRY_PENDING"
    assert record.recovery_disposition == "SAFE_RETRY"
    store.close()
