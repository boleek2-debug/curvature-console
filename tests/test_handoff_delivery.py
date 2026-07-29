"""Tests for B5.5C one-shot controlled handoff delivery."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from curvature_console.infrastructure.handoff import (
    HandoffStatus,
    create_handoff,
)
from curvature_console.main import create_application
from curvature_console.presentation.main_window import (
    MainWindow,
    PendingBrowserExchange,
)


def _approved_handoff():
    return create_handoff(
        handoff_id="handoff-1",
        request_id="request-1",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Implement this.",
    ).transition(HandoffStatus.PENDING_APPROVAL).transition(
        HandoffStatus.APPROVED
    ).transition(HandoffStatus.SENT)


def test_success_records_received_and_answered_timeline(tmp_path) -> None:
    create_application(["handoff-delivery-success-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    window.state_store.save_handoff(_approved_handoff())
    pending = PendingBrowserExchange(
        request_id="browser-1",
        department_id="core",
        user_task="handoff",
        handoff_id="handoff-1",
    )

    window._record_handoff_answer(pending, "Core response.")

    restored = window.state_store.load_handoff("handoff-1")
    assert restored is not None
    assert restored.status is HandoffStatus.ANSWERED
    assert restored.timeline[-1].body == "Core response."
    window.close()


def test_failure_moves_sent_handoff_to_held(tmp_path) -> None:
    create_application(["handoff-delivery-failure-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    window.state_store.save_handoff(_approved_handoff())
    pending = PendingBrowserExchange(
        request_id="browser-1",
        department_id="core",
        user_task="handoff",
        handoff_id="handoff-1",
    )

    window._hold_failed_handoff(pending, "Browser unavailable.")

    restored = window.state_store.load_handoff("handoff-1")
    assert restored is not None
    assert restored.status is HandoffStatus.HELD
    assert "Browser unavailable" in restored.timeline[-1].body
    window.close()
