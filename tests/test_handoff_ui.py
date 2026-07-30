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


def test_dialog_is_presented_as_supervised_communication_hub(tmp_path) -> None:
    create_application(["curvature-console-handoff-hub-label-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    dialog = HandoffControlsDialog(store)

    assert dialog.windowTitle() == "Supervised Communication Hub"
    labels = [label.text() for label in dialog.findChildren(type(dialog.status_label))]
    assert any("Department-generated drafts appear here automatically" in text for text in labels)

    dialog.close()
    store.close()


def test_generated_pending_handoff_skips_request_approval_control(
    tmp_path,
) -> None:
    from curvature_console.infrastructure.handoff import create_handoff

    create_application(["curvature-console-generated-pending-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    record = create_handoff(
        request_id="proposal-1",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="# Generated proposal\n\nImplement it.",
    ).transition(HandoffStatus.PENDING_APPROVAL)
    store.save_handoff(record)

    dialog = HandoffControlsDialog(store)

    assert dialog.selected_record is not None
    assert dialog.selected_record.status is HandoffStatus.PENDING_APPROVAL
    assert not dialog.submit_button.isEnabled()
    assert dialog.approve_button.isEnabled()
    assert not dialog.deliver_button.isEnabled()

    dialog.close()
    store.close()


def test_delivery_confirmation_is_resizable_and_scrollable() -> None:
    from PySide6.QtWidgets import QDialogButtonBox, QPlainTextEdit

    from curvature_console.presentation.handoff_controls_dialog import (
        HandoffDeliveryConfirmationDialog,
    )

    create_application(["curvature-console-delivery-confirmation-test"])
    dialog = HandoffDeliveryConfirmationDialog(
        target_department_id="core",
        handoff_title="Verify long delivery",
        handoff_message="\n".join(f"Line {index}" for index in range(300)),
    )

    details = dialog.findChild(QPlainTextEdit, "handoffDeliveryDetails")
    buttons = dialog.findChild(QDialogButtonBox, "handoffDeliveryButtons")

    assert dialog.minimumWidth() <= dialog.width()
    assert dialog.minimumHeight() <= dialog.height()
    assert dialog.isSizeGripEnabled()
    assert details is not None
    assert details.isReadOnly()
    assert details.verticalScrollBar().maximum() > 0
    assert buttons is not None
    assert buttons.button(QDialogButtonBox.StandardButton.Yes) is not None
    assert buttons.button(QDialogButtonBox.StandardButton.Cancel) is not None

    dialog.close()


def test_delivery_progress_dialog_shows_stage_and_elapsed_feedback() -> None:
    from PySide6.QtWidgets import QLabel, QProgressBar

    from curvature_console.presentation.handoff_controls_dialog import (
        HandoffDeliveryProgressDialog,
    )

    create_application(["curvature-console-delivery-progress-test"])
    dialog = HandoffDeliveryProgressDialog(
        target_department_id="core",
        handoff_title="Verify controlled delivery",
    )

    stage = dialog.findChild(QLabel, "handoffProgressStage")
    elapsed = dialog.findChild(QLabel, "handoffProgressElapsed")
    progress = dialog.findChild(QProgressBar, "handoffProgressBar")

    assert stage is not None
    assert elapsed is not None
    assert progress is not None
    assert progress.minimum() == 0
    assert progress.maximum() == 0

    dialog.set_stage("Waiting for response")
    assert stage.text() == "Waiting for response…"
    assert elapsed.text().startswith("Elapsed: ")

    dialog.finish()


def test_reply_decision_controls_are_only_enabled_for_captured_reply(
    tmp_path,
) -> None:
    from curvature_console.infrastructure.handoff import create_handoff

    create_application(["curvature-console-reply-decision-controls-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    record = create_handoff(
        handoff_id="handoff-reply-1",
        request_id="request-reply-1",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Plan the implementation.",
    )
    record = record.transition(HandoffStatus.PENDING_APPROVAL)
    record = record.transition(HandoffStatus.APPROVED)
    record = record.transition(HandoffStatus.SENT)
    record = record.transition(HandoffStatus.RECEIVED)
    record = record.transition(HandoffStatus.AWAITING_USER_DECISION)
    record = record.append_message("core", "Task accepted. Plan follows.")
    store.save_handoff(record)

    dialog = HandoffControlsDialog(store)

    assert dialog.continue_button.isEnabled()
    assert dialog.return_button.isEnabled()
    assert dialog.close_button.isEnabled()
    assert not dialog.deliver_button.isEnabled()

    dialog.close()
    store.close()


def test_return_button_emits_only_for_reply_awaiting_decision(tmp_path) -> None:
    from curvature_console.infrastructure.handoff import create_handoff

    create_application(["curvature-console-return-control-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    record = create_handoff(
        handoff_id="handoff-return-ui",
        request_id="request-return-ui",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Return the plan.",
    )
    record = record.transition(HandoffStatus.PENDING_APPROVAL)
    record = record.transition(HandoffStatus.APPROVED)
    record = record.transition(HandoffStatus.SENT)
    record = record.transition(HandoffStatus.RECEIVED)
    record = record.transition(HandoffStatus.AWAITING_USER_DECISION)
    record = record.append_message("core", "Execution plan.")
    store.save_handoff(record)

    dialog = HandoffControlsDialog(store)
    emitted: list[str] = []
    dialog.return_requested.connect(emitted.append)
    dialog.return_selected()

    assert emitted == ["handoff-return-ui"]
    assert store.load_handoff("handoff-return-ui").status is HandoffStatus.AWAITING_USER_DECISION

    dialog.close()
    store.close()


def test_open_hub_refreshes_after_handoff_reply_is_recorded(tmp_path) -> None:
    from curvature_console.infrastructure.handoff import create_handoff
    from curvature_console.presentation.main_window import PendingBrowserExchange

    create_application(["curvature-console-live-hub-refresh-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    record = create_handoff(
        handoff_id="handoff-live-refresh",
        request_id="request-live-refresh",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Return a plan.",
    )
    record = record.transition(HandoffStatus.PENDING_APPROVAL)
    record = record.transition(HandoffStatus.APPROVED)
    record = record.transition(HandoffStatus.SENT)
    window.state_store.save_handoff(record)

    dialog = HandoffControlsDialog(window.state_store, parent=window)
    dialog.show()
    window._handoff_controls_dialog = dialog
    pending = PendingBrowserExchange(
        request_id="browser-live-refresh",
        department_id="core",
        user_task="handoff",
        handoff_id=record.handoff_id,
    )

    window._record_handoff_answer(pending, "Plan ready.")

    assert dialog.selected_record is not None
    assert dialog.selected_record.handoff_id == record.handoff_id
    assert dialog.selected_record.status is HandoffStatus.AWAITING_USER_DECISION
    assert "Plan ready." in dialog.timeline_view.toPlainText()

    dialog.close()
    window.state_store.close()
