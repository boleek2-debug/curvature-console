"""Tests for the shared sequential Browser Bridge queue."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow


def _window(tmp_path: Path) -> MainWindow:
    create_application(["curvature-console-queue-test"])
    return MainWindow(
        data_directory=tmp_path / "data",
        state_path=tmp_path / "state.sqlite3",
        repository_roots={"curvature-console": tmp_path, "Curvature": tmp_path},
    )


def _worker(department_id: str) -> Mock:
    worker = Mock()
    worker.request.department_id = department_id
    return worker


def test_queue_starts_first_worker_and_keeps_second_waiting(tmp_path: Path) -> None:
    window = _window(tmp_path)
    first = _worker("project")
    second = _worker("console-development")

    window._enqueue_browser_worker(first)
    window._enqueue_browser_worker(second)

    first.start.assert_called_once_with()
    second.start.assert_not_called()
    assert window._browser_worker is first
    assert list(window._browser_queue) == [second]
    assert window.browser_queue_label.text() == "Bridge active: project · 1 waiting"
    window._browser_worker = None
    window._browser_queue.clear()
    window.close()


def test_finished_worker_starts_next_queued_exchange(tmp_path: Path) -> None:
    window = _window(tmp_path)
    first = _worker("core")
    second = _worker("research")
    window._browser_worker = first
    window._browser_queue.append(second)

    window._clear_browser_worker()

    first.deleteLater.assert_called_once_with()
    second.start.assert_called_once_with()
    assert window._browser_worker is second
    assert not window._browser_queue
    assert window.browser_queue_label.text() == "Bridge active: research · 0 waiting"
    window._browser_worker = None
    window.close()


def test_idle_queue_status_is_explicit(tmp_path: Path) -> None:
    window = _window(tmp_path)
    window._refresh_browser_queue_status()
    assert window.browser_queue_label.text() == "Bridge queue: idle"
    window.close()


def test_handoff_progress_opens_only_when_queued_worker_becomes_active(
    tmp_path: Path,
) -> None:
    window = _window(tmp_path)
    active = _worker("project")
    active.request.request_id = "active-1"
    queued = _worker("core")
    queued.request.request_id = "handoff-queued-1"
    window._browser_worker = active
    window._handoff_progress_specs["handoff-queued-1"] = (
        "core",
        "# Queued handoff",
    )
    window._browser_queue.append(queued)

    window._clear_browser_worker()

    assert window._browser_worker is queued
    assert window._handoff_progress_request_id == "handoff-queued-1"
    assert window._handoff_progress_dialog is not None
    window._finish_handoff_progress("handoff-queued-1")
    window._browser_worker = None
    window.close()


def test_abort_removes_oldest_queued_request_for_department(
    tmp_path: Path,
) -> None:
    window = _window(tmp_path)
    active = _worker("project")
    active.request.request_id = "active-1"
    queued = _worker("core")
    queued.request.request_id = "queued-core-1"
    window._browser_worker = active
    window._browser_queue.append(queued)
    window._handoff_progress_specs["queued-core-1"] = (
        "core",
        "# Queued operation",
    )

    window.abort_browser_operation("core")

    assert not window._browser_queue
    assert "queued-core-1" not in window._handoff_progress_specs
    queued.deleteLater.assert_called_once_with()
    window._browser_worker = None
    window.close()


def test_queue_persists_browser_exchange_before_worker_execution(
    tmp_path: Path,
) -> None:
    from curvature_console.presentation.main_window import PendingBrowserExchange

    window = _window(tmp_path)
    active = _worker("project")
    active.request.request_id = "exchange-active"
    active.request.conversation_url = "https://chatgpt.com/c/project"
    active.request.confirmation_marker = "CURVATURE_REQUEST_ID: exchange-active"
    queued = _worker("core")
    queued.request.request_id = "exchange-queued"
    queued.request.conversation_url = "https://chatgpt.com/c/core"
    queued.request.confirmation_marker = "CURVATURE_REQUEST_ID: exchange-queued"

    window._pending_exchanges["exchange-active"] = PendingBrowserExchange(
        request_id="exchange-active",
        department_id="project",
        user_task="Continue operator review.",
        operational_conversation_id="operational-chain-1",
        operational_operator_followup=True,
    )
    window._pending_exchanges["exchange-queued"] = PendingBrowserExchange(
        request_id="exchange-queued",
        department_id="core",
        user_task="Run operational work.",
        operational_conversation_id="operational-chain-1",
        automatic_operational_request=True,
    )

    window._enqueue_browser_worker(active)
    window._enqueue_browser_worker(queued)

    active_record = window.state_store.load_browser_exchange("exchange-active")
    queued_record = window.state_store.load_browser_exchange("exchange-queued")

    assert active_record is not None
    assert active_record.state == "STARTED"
    assert active_record.exchange_type == "OPERATOR_FOLLOWUP"
    assert active_record.workflow_id == "operational-chain-1"
    assert queued_record is not None
    assert queued_record.state == "QUEUED"
    assert queued_record.exchange_type == "OPERATIONAL_REQUEST"
    assert queued_record.workflow_id == "operational-chain-1"
    active.start.assert_called_once_with()
    queued.start.assert_not_called()

    window._browser_worker = None
    window._browser_queue.clear()
    window.close()


def test_abort_queued_request_persists_cancelled_exchange(
    tmp_path: Path,
) -> None:
    from curvature_console.presentation.main_window import PendingBrowserExchange

    window = _window(tmp_path)
    active = _worker("project")
    active.request.request_id = "active-2"
    queued = _worker("core")
    queued.request.request_id = "queued-core-ledger"
    queued.request.conversation_url = "https://chatgpt.com/c/core"
    queued.request.confirmation_marker = None
    window._browser_worker = active
    window._pending_exchanges["queued-core-ledger"] = PendingBrowserExchange(
        request_id="queued-core-ledger",
        department_id="core",
        user_task="Queued task",
    )

    window._enqueue_browser_worker(queued)
    window.abort_browser_operation("core")

    record = window.state_store.load_browser_exchange("queued-core-ledger")
    assert record is not None
    assert record.state == "CANCELLED"
    assert record.cancel_submitted is False
    assert record.completed_at
    assert record.failure_reason == "Queued request cancelled by operator."

    window._browser_worker = None
    window.close()


def test_queued_operational_cancel_blocks_conversation_immediately(
    tmp_path: Path,
) -> None:
    from curvature_console.presentation.main_window import PendingBrowserExchange

    window = _window(tmp_path)
    window.state_store.create_operational_conversation(
        conversation_id="operational-cancel-queued",
        source_request_id="source-cancel-queued",
        title="Queued operational work",
        participants=("project", "core"),
        status="RUNNING",
    )

    active = _worker("project")
    active.request.request_id = "active-other"
    queued = _worker("core")
    queued.request.request_id = "queued-operational-cancel"
    queued.request.conversation_url = "https://chatgpt.com/c/core"
    queued.request.confirmation_marker = None
    window._browser_worker = active
    window._pending_exchanges["queued-operational-cancel"] = PendingBrowserExchange(
        request_id="queued-operational-cancel",
        department_id="core",
        user_task="Queued operational work",
        operational_conversation_id="operational-cancel-queued",
        automatic_operational_request=True,
    )

    window._enqueue_browser_worker(queued)
    window.abort_browser_operation("core")

    conversation = window.state_store.load_operational_conversation(
        "operational-cancel-queued"
    )
    assert conversation is not None
    assert conversation.status == "BLOCKED"
    assert conversation.attention_kind == "BLOCKER"
    assert conversation.attention_reason == "Queued request cancelled by operator."

    window._browser_worker = None
    window.close()


def test_operational_browser_failure_blocks_conversation_immediately(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from PySide6.QtWidgets import QMessageBox

    from curvature_console.presentation.main_window import PendingBrowserExchange

    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    window = _window(tmp_path)
    window.state_store.create_operational_conversation(
        conversation_id="operational-failure",
        source_request_id="source-failure",
        title="Operational work",
        participants=("project", "core"),
        status="WAITING_SOURCE",
    )
    request_id = "operational-failure-request"
    window._pending_exchanges[request_id] = PendingBrowserExchange(
        request_id=request_id,
        department_id="project",
        user_task="Return operational work",
        operational_conversation_id="operational-failure",
        automatic_operational_return=True,
    )
    window.state_store.create_browser_exchange(
        request_id=request_id,
        department_id="project",
        exchange_type="OPERATIONAL_RETURN",
        workflow_id="operational-failure",
        requested_conversation_url="https://chatgpt.com/c/project",
        confirmation_marker=None,
    )

    window._handle_browser_failure(
        request_id,
        "project",
        "Synthetic bridge failure",
    )

    conversation = window.state_store.load_operational_conversation(
        "operational-failure"
    )
    assert conversation is not None
    assert conversation.status == "BLOCKED"
    assert conversation.attention_kind == "BLOCKER"
    assert conversation.attention_reason == "Synthetic bridge failure"
    messages = window.state_store.load_operational_messages("operational-failure")
    assert any(
        "Browser Bridge transport interrupted: Synthetic bridge failure"
        in message.body
        for message in messages
    )

    window.close()
