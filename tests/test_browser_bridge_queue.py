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
