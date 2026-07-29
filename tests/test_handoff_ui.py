"""UI tests for B5.5B supervised Bridge Controls."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from curvature_console.infrastructure.handoff import HandoffStatus
from curvature_console.infrastructure.state_store import SQLiteStateStore
from curvature_console.main import create_application
from curvature_console.presentation.handoff_controls_dialog import (
    HandoffControlsDialog,
)
from curvature_console.presentation.main_window import MainWindow


def test_main_window_exposes_bridge_controls_button(tmp_path) -> None:
    create_application(["curvature-console-handoff-controls-button-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )

    assert window.handoff_controls_button.text() == "Bridge Controls"
    assert window.handoff_controls_button.isEnabled()
    window.close()


def test_dialog_creates_approves_and_persists_visible_timeline(
    tmp_path,
) -> None:
    create_application(["curvature-console-handoff-controls-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    dialog = HandoffControlsDialog(store)

    dialog.source_combo.setCurrentIndex(
        dialog.source_combo.findData("project")
    )
    dialog.target_combo.setCurrentIndex(
        dialog.target_combo.findData("core")
    )
    dialog.message_editor.setPlainText("Implement approved schema.")
    dialog.create_draft()

    record = dialog.selected_record
    assert record is not None
    assert record.status is HandoffStatus.DRAFT

    dialog._transition_selected(HandoffStatus.PENDING_APPROVAL)
    dialog._transition_selected(HandoffStatus.APPROVED)

    restored = store.load_handoff(record.handoff_id)
    assert restored is not None
    assert restored.status is HandoffStatus.APPROVED
    assert [item.body for item in restored.timeline] == [
        "Draft created: Implement approved schema.",
        "Control action: pending_approval",
        "Control action: approved",
    ]
    assert "Control action: approved" in dialog.timeline_view.toPlainText()

    dialog.close()
    store.close()


def test_deliver_button_only_emits_for_approved_handoff(tmp_path) -> None:
    create_application(["curvature-console-handoff-deliver-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    dialog = HandoffControlsDialog(store)
    emitted: list[str] = []
    dialog.deliver_requested.connect(emitted.append)

    dialog.message_editor.setPlainText("Engage.")
    dialog.create_draft()
    record = dialog.selected_record
    assert record is not None
    assert not dialog.deliver_button.isEnabled()

    dialog._transition_selected(HandoffStatus.PENDING_APPROVAL)
    dialog._transition_selected(HandoffStatus.APPROVED)
    assert dialog.deliver_button.isEnabled()

    dialog.deliver_selected()
    assert emitted == [record.handoff_id]
    assert store.load_handoff(record.handoff_id).status is HandoffStatus.APPROVED

    dialog.close()
    store.close()


def test_dialog_exposes_one_explicit_deliver_control(tmp_path) -> None:
    create_application(["curvature-console-handoff-no-send-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    dialog = HandoffControlsDialog(store)

    button_texts = {
        button.text()
        for button in dialog.findChildren(type(dialog.new_button))
    }

    assert "Send" not in button_texts
    assert "Deliver" in button_texts
    dialog.close()
    store.close()
