"""Tests for workspace configuration and context loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from curvature_console.configuration.workspace_config import (
    WorkspaceConfigError,
    load_workspace_config,
)
from curvature_console.infrastructure.context_loader import WorkspaceContextLoader


def test_workspace_config_loads_valid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "core.yaml"
    config_path.write_text(
        "\n".join(
            [
                "department_id: core",
                "title: Curvature Core",
                f"role_file: {tmp_path / 'core.md'}",
                f"repository_path: {tmp_path / 'repo'}",
                "documents:",
                "  - HANDOFF.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_workspace_config(config_path)

    assert config.department_id == "core"
    assert config.title == "Curvature Core"
    assert config.documents == (Path("HANDOFF.md"),)


def test_workspace_config_rejects_missing_documents(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        "\n".join(
            [
                "department_id: core",
                "title: Curvature Core",
                "role_file: role.md",
                "repository_path: repo",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(WorkspaceConfigError, match="documents"):
        load_workspace_config(config_path)


def test_context_loader_reads_role_and_repository_documents(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    role = tmp_path / "core.md"
    role.write_text("Core role", encoding="utf-8")

    handoff = repository / "HANDOFF.md"
    handoff.write_text("Current state", encoding="utf-8")

    config_path = tmp_path / "core.yaml"
    config_path.write_text(
        "\n".join(
            [
                "department_id: core",
                "title: Curvature Core",
                f"role_file: {role}",
                f"repository_path: {repository}",
                "documents:",
                "  - HANDOFF.md",
            ]
        ),
        encoding="utf-8",
    )

    result = WorkspaceContextLoader().load(
        load_workspace_config(config_path)
    )

    assert result.loaded_count == 2
    assert result.errors == ()
    assert [document.label for document in result.documents] == [
        "ROLE",
        "HANDOFF.md",
    ]
    assert "Core role" in result.preview_text()
    assert "Current state" in result.preview_text()


def test_context_loader_records_missing_document_errors(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    role = tmp_path / "research.md"
    role.write_text("Research role", encoding="utf-8")

    config_path = tmp_path / "research.yaml"
    config_path.write_text(
        "\n".join(
            [
                "department_id: research",
                "title: Curvature Research",
                f"role_file: {role}",
                f"repository_path: {repository}",
                "documents:",
                "  - LANGUAGE.md",
            ]
        ),
        encoding="utf-8",
    )

    result = WorkspaceContextLoader().load(
        load_workspace_config(config_path)
    )

    assert result.loaded_count == 1
    assert len(result.errors) == 1
    assert "Document not found: LANGUAGE.md" in result.errors[0]
