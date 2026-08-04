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
