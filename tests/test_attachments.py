"""Tests for per-department attachment queues."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QImage

from curvature_console.main import create_application
from curvature_console.presentation.attachment_list import AttachmentList
from curvature_console.presentation.main_window import MainWindow


@pytest.fixture
def application():
    return create_application(["curvature-console-attachment-test"])


def test_each_department_has_an_independent_attachment_queue(application) -> None:
    window = MainWindow()
    window.show()

    queues = [
        panel.attachment_list for panel in window.department_panels.values()
    ]

    assert all(isinstance(queue, AttachmentList) for queue in queues)
    assert len({id(queue) for queue in queues}) == 3
    assert all(queue.records == () for queue in queues)

    window.close()


def test_files_can_be_added_without_crossing_departments(
    application,
    tmp_path: Path,
) -> None:
    project_file = tmp_path / "decision.md"
    project_file.write_text("Project decision", encoding="utf-8")

    research_file = tmp_path / "paper.pdf"
    research_file.write_bytes(b"%PDF-test")

    window = MainWindow()

    project_queue = window.department_panels["project"].attachment_list
    research_queue = window.department_panels["research"].attachment_list
    core_queue = window.department_panels["core"].attachment_list

    project_queue.add_paths([project_file])
    research_queue.add_paths([research_file])

    assert [record.name for record in project_queue.records] == ["decision.md"]
    assert [record.name for record in research_queue.records] == ["paper.pdf"]
    assert core_queue.records == ()

    window.close()


def test_duplicate_and_missing_files_are_ignored(
    application,
    tmp_path: Path,
) -> None:
    existing = tmp_path / "log.txt"
    existing.write_text("test", encoding="utf-8")

    queue = AttachmentList("core")
    queue.add_paths([existing, existing, tmp_path / "missing.txt"])

    assert len(queue.records) == 1
    assert queue.records[0].name == "log.txt"


def test_selected_attachment_can_be_removed(
    application,
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("1", encoding="utf-8")
    second.write_text("2", encoding="utf-8")

    queue = AttachmentList("research")
    queue.add_paths([first, second])
    queue.list_widget.item(0).setSelected(True)

    queue.remove_selected()

    assert [record.name for record in queue.records] == ["second.txt"]


def test_screenshot_can_be_pasted_from_clipboard(application) -> None:
    image = QImage(32, 32, QImage.Format.Format_ARGB32)
    image.fill(0xFF336699)
    application.clipboard().setImage(image)

    queue = AttachmentList("project")

    assert queue.paste_screenshot_from_clipboard() is True
    assert len(queue.records) == 1
    assert queue.records[0].temporary is True
    assert queue.records[0].path.exists()
    assert queue.records[0].suffix == "png"

    temporary_path = queue.records[0].path
    queue.clear_attachments()

    assert queue.records == ()
    assert not temporary_path.exists()
