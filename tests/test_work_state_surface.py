"""Tests for the CDU-004B8B read-only work-state surface."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow


def _window(tmp_path: Path) -> MainWindow:
    create_application(["curvature-console-work-state-test"])
    return MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )


def test_work_surface_is_opt_in_and_legacy_departments_remain_default(
    tmp_path: Path,
) -> None:
    window = _window(tmp_path)

    assert window.main_surface_stack.currentWidget() is window.splitter
    assert window.work_surface_button.isEnabled()
    assert not window.departments_surface_button.isEnabled()
    assert window.splitter.count() == 3
    assert set(window.department_panels) == {"project", "core", "research"}

    window.show_work_surface()

    assert window.main_surface_stack.currentWidget() is window.work_state_surface
    assert not window.work_surface_button.isEnabled()
    assert window.departments_surface_button.isEnabled()

    window.show_departments_surface()
    assert window.main_surface_stack.currentWidget() is window.splitter
    window.close()


def test_work_surface_reads_attention_and_active_operational_state(
    tmp_path: Path,
) -> None:
    window = _window(tmp_path)
    store = window.state_store

    store.create_operational_conversation(
        conversation_id="active-work",
        source_request_id="source-active",
        title="Build Chronicle slice",
        participants=("project", "core"),
        status="RUNNING",
    )
    store.create_operational_conversation(
        conversation_id="blocked-work",
        source_request_id="source-blocked",
        title="Research evidence intake",
        participants=("project", "research"),
        status="BLOCKED",
    )
    store.update_operational_attention(
        "blocked-work",
        attention_kind="BLOCKER",
        attention_reason="Source unavailable",
    )

    window.work_state_surface.refresh()

    attention = [
        window.work_state_surface.attention_list.item(i).text()
        for i in range(window.work_state_surface.attention_list.count())
    ]
    active = [
        window.work_state_surface.active_list.item(i).text()
        for i in range(window.work_state_surface.active_list.count())
    ]

    assert any("Research evidence intake" in row for row in attention)
    assert any("Source unavailable" in row for row in attention)
    assert any("Build Chronicle slice" in row for row in active)
    window.close()


def test_work_surface_exposes_recovery_state_without_retrying(
    tmp_path: Path,
) -> None:
    window = _window(tmp_path)
    store = window.state_store

    store.create_browser_exchange(
        request_id="recovery-exchange",
        department_id="core",
        exchange_type="TASK",
        workflow_id=None,
        requested_conversation_url="https://chatgpt.com/c/core",
        confirmation_marker=None,
    )
    store.reconcile_interrupted_browser_exchanges()

    window.work_state_surface.refresh()

    attention = [
        window.work_state_surface.attention_list.item(i).text()
        for i in range(window.work_state_surface.attention_list.count())
    ]
    record = store.load_browser_exchange("recovery-exchange")

    assert record is not None
    assert record.state == "RETRY_PENDING"
    assert record.recovery_disposition == "SAFE_RETRY"
    assert any("RETRY_PENDING" in row for row in attention)
    assert window._browser_worker is None
    assert not window._browser_queue
    window.close()


def test_work_surface_is_read_only_and_has_no_apply_or_send_controls(
    tmp_path: Path,
) -> None:
    window = _window(tmp_path)
    surface = window.work_state_surface

    assert (
        surface.findChild(type(window.restore_button), "workStateRefreshButton")
        is not None
    )
    assert surface.findChild(type(window.restore_button), "applyButton") is None
    assert surface.findChild(type(window.restore_button), "sendTaskButton") is None
    assert "view only" in surface.footer_label.text().lower()
    window.close()


def test_result_ready_is_attention_but_not_active_work(tmp_path: Path) -> None:
    window = _window(tmp_path)
    store = window.state_store

    store.create_operational_conversation(
        conversation_id="ready-result",
        source_request_id="source-ready",
        title="Completed Chronicle result",
        participants=("project", "core"),
        status="RESULT_READY",
    )
    store.update_operational_attention(
        "ready-result",
        attention_kind="RESULT",
        attention_reason="Completed result.",
    )

    window.work_state_surface.refresh()

    attention = [
        window.work_state_surface.attention_list.item(i).text()
        for i in range(window.work_state_surface.attention_list.count())
    ]
    active = [
        window.work_state_surface.active_list.item(i).text()
        for i in range(window.work_state_surface.active_list.count())
    ]

    assert any("RESULT READY — acknowledge & close" in row for row in attention)
    assert any("Completed Chronicle result" in row for row in attention)
    assert not any("Completed Chronicle result" in row for row in active)
    assert window.work_state_surface.active_summary.findChild(
        type(window.work_state_surface.footer_label), "workStateSummaryValue"
    ).text() == "0"
    window.close()


def _persist_handoff_with_status(store, *, handoff_id: str, status):
    from curvature_console.infrastructure.handoff import HandoffStatus, create_handoff

    record = create_handoff(
        handoff_id=handoff_id,
        request_id=f"request-{handoff_id}",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="B8B handoff classification test.",
    )
    paths = {
        HandoffStatus.HELD: (
            HandoffStatus.PENDING_APPROVAL,
            HandoffStatus.HELD,
        ),
        HandoffStatus.RETURNED: (
            HandoffStatus.PENDING_APPROVAL,
            HandoffStatus.APPROVED,
            HandoffStatus.SENT,
            HandoffStatus.RECEIVED,
            HandoffStatus.AWAITING_USER_DECISION,
            HandoffStatus.RETURN_SENT,
            HandoffStatus.RETURNED,
        ),
        HandoffStatus.IN_PROGRESS: (
            HandoffStatus.PENDING_APPROVAL,
            HandoffStatus.APPROVED,
            HandoffStatus.SENT,
            HandoffStatus.RECEIVED,
            HandoffStatus.AWAITING_USER_DECISION,
            HandoffStatus.IN_PROGRESS,
        ),
    }
    for next_status in paths[status]:
        record = record.transition(next_status)
    store.save_handoff(record)
    return record


def test_held_and_returned_handoffs_are_attention_not_active(tmp_path: Path) -> None:
    from curvature_console.infrastructure.handoff import HandoffStatus

    window = _window(tmp_path)
    store = window.state_store
    _persist_handoff_with_status(
        store,
        handoff_id="held-handoff",
        status=HandoffStatus.HELD,
    )
    _persist_handoff_with_status(
        store,
        handoff_id="returned-handoff",
        status=HandoffStatus.RETURNED,
    )

    window.work_state_surface.refresh()

    attention = [
        window.work_state_surface.attention_list.item(i).text()
        for i in range(window.work_state_surface.attention_list.count())
    ]
    active = [
        window.work_state_surface.active_list.item(i).text()
        for i in range(window.work_state_surface.active_list.count())
    ]

    assert any("HANDOFF HELD — review or stop" in row for row in attention)
    assert any("HANDOFF RETURNED — close or continue" in row for row in attention)
    assert not any("held-handoff" in row for row in active)
    assert not any("HANDOFF held" in row for row in active)
    assert not any("HANDOFF returned" in row for row in active)
    assert window.work_state_surface.active_summary.findChild(
        type(window.work_state_surface.footer_label), "workStateSummaryValue"
    ).text() == "0"
    assert window.work_state_surface.attention_summary.findChild(
        type(window.work_state_surface.footer_label), "workStateSummaryValue"
    ).text() == "2"
    window.close()


def test_in_progress_handoff_remains_active_work(tmp_path: Path) -> None:
    from curvature_console.infrastructure.handoff import HandoffStatus

    window = _window(tmp_path)
    store = window.state_store
    _persist_handoff_with_status(
        store,
        handoff_id="active-handoff",
        status=HandoffStatus.IN_PROGRESS,
    )

    window.work_state_surface.refresh()

    active = [
        window.work_state_surface.active_list.item(i).text()
        for i in range(window.work_state_surface.active_list.count())
    ]
    attention = [
        window.work_state_surface.attention_list.item(i).text()
        for i in range(window.work_state_surface.attention_list.count())
    ]

    assert any("HANDOFF in_progress: project → core" in row for row in active)
    assert not any("IN_PROGRESS" in row for row in attention)
    assert window.work_state_surface.active_summary.findChild(
        type(window.work_state_surface.footer_label), "workStateSummaryValue"
    ).text() == "1"
    window.close()
