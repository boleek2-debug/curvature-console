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
