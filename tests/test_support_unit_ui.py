"""UI tests for Curvature Support Unit."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow
from curvature_console.presentation.support_unit_dialog import SupportUnitDialog


def _repository(tmp_path: Path, name: str) -> Path:
    repository = tmp_path / name
    repository.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Curvature Test"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repository,
        check=True,
    )
    (repository / "README.md").write_text(name, encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "baseline"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=repository,
        check=True,
    )
    return repository


def test_support_unit_button_is_next_to_bridge_controls(tmp_path: Path) -> None:
    create_application(["curvature-console-support-unit-test"])
    console = _repository(tmp_path, "console")
    project = _repository(tmp_path, "project")
    window = MainWindow(
        data_directory=tmp_path / "data",
        state_path=tmp_path / "state.sqlite3",
        repository_roots={
            "curvature-console": console,
            "Curvature": project,
        },
    )

    assert window.support_unit_button.text() == "Support Unit"
    assert window.support_unit_button.objectName() == "supportUnitButton"
    assert window.handoff_controls_button.parent() is window.support_unit_button.parent()
    window.close()


def test_support_unit_dialog_renders_repository_state(tmp_path: Path) -> None:
    create_application(["curvature-console-support-dialog-test"])
    console = _repository(tmp_path, "console")
    dialog = SupportUnitDialog(
        repository_roots={"curvature-console": console},
        data_directory=tmp_path / "data",
    )

    assert "Repositories clean: 1/1" in dialog.summary_label.text()
    assert "Repository: curvature-console" in dialog.report_view.toPlainText()
    assert not dialog.open_log_button.isEnabled()
    dialog.close()
