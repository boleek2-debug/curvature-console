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
    )
    store.close()

    reopened = SQLiteStateStore(database)
    state = reopened.load_department_state("core")

    assert state is not None
    assert state.conversation_text == "Core transcript"
    assert state.draft_text == "Unsaved Core draft"

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
