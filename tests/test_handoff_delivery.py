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


def test_department_response_creates_reviewable_draft_without_delivery(
    tmp_path,
) -> None:
    create_application(["handoff-proposal-intake-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    pending = PendingBrowserExchange(
        request_id="browser-project-1",
        department_id="project",
        user_task="Define the next implementation step.",
    )
    response = '''Project analysis complete.

BEGIN_CURVATURE_HANDOFF_PROPOSAL
{
  "schema_version": 1,
  "target_department_id": "core",
  "title": "Implement proposal intake",
  "reason": "Core owns implementation.",
  "task": "Implement the approved intake scope.",
  "relevant_context": "Bridge Controls already persists handoffs.",
  "expected_output": "Source, tests and validation.",
  "acceptance_criteria": ["Draft appears in the hub", "No automatic delivery"]
}
END_CURVATURE_HANDOFF_PROPOSAL'''

    captured, errors = window._capture_department_handoff_proposals(
        pending,
        response,
    )

    assert captured == 1
    assert errors == ()
    records = window.state_store.load_handoffs()
    assert len(records) == 1
    record = records[0]
    assert record.status is HandoffStatus.PENDING_APPROVAL
    assert record.source_department_id == "project"
    assert record.target_department_id == "core"
    assert "# Implement proposal intake" in record.user_visible_message
    assert "queued for operator approval" in record.timeline[-1].body
    window.close()


def test_proposal_intake_is_idempotent_for_one_browser_response(tmp_path) -> None:
    create_application(["handoff-proposal-idempotency-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    pending = PendingBrowserExchange(
        request_id="browser-core-1",
        department_id="core",
        user_task="Assess research dependency.",
    )
    response = '''BEGIN_CURVATURE_HANDOFF_PROPOSAL
{"schema_version":1,"target_department_id":"research","title":"Check evidence","reason":"Research owns evidence assessment.","task":"Assess the cited evidence.","relevant_context":"Core found an unresolved claim.","expected_output":"Evidence assessment.","acceptance_criteria":["Confidence is stated"]}
END_CURVATURE_HANDOFF_PROPOSAL'''

    first = window._capture_department_handoff_proposals(pending, response)
    second = window._capture_department_handoff_proposals(pending, response)

    assert first == (1, ())
    assert second == (0, ())
    assert len(window.state_store.load_handoffs()) == 1
    window.close()
