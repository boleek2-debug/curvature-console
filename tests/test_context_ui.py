"""Tests for context controls in the three-panel UI."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow


def _write_workspace(
    config_directory: Path,
    repository: Path,
    roles_directory: Path,
    department_id: str,
) -> None:
    role = roles_directory / f"{department_id}.md"
    role.write_text(f"{department_id} role", encoding="utf-8")

    (config_directory / f"{department_id}.yaml").write_text(
        "\n".join(
            [
                f"department_id: {department_id}",
                f"title: {department_id.title()}",
                f"role_file: {role}",
                f"repository_path: {repository}",
                "documents:",
                "  - HANDOFF.md",
            ]
        ),
        encoding="utf-8",
    )


def test_main_window_loads_context_for_all_three_departments(
    tmp_path: Path,
) -> None:
    create_application(["curvature-console-context-ui-test"])

    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "HANDOFF.md").write_text(
        "Shared project state",
        encoding="utf-8",
    )

    roles = tmp_path / "roles"
    roles.mkdir()

    configs = tmp_path / "configs"
    configs.mkdir()

    for department_id in ("project", "core", "research"):
        _write_workspace(
            configs,
            repository,
            roles,
            department_id,
        )

    window = MainWindow(config_directory=configs)

    assert set(window.workspace_configs) == {"project", "core", "research"}
    assert set(window.context_results) == {"project", "core", "research"}

    for department_id, panel in window.department_panels.items():
        result = window.context_results[department_id]
        assert result.loaded_count == 2
        assert panel.context_files.count() == 2
        assert panel.preview_context_button.isEnabled()
        assert "2 loaded" in panel.context_label.text()

    window.close()
