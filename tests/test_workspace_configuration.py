"""Tests for workspace configuration and context loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from curvature_console.configuration.workspace_config import (
    WorkspaceConfigError,
    load_workspace_config,
)
from curvature_console.infrastructure.context_loader import WorkspaceContextLoader


def test_workspace_config_loads_legacy_yaml(tmp_path: Path) -> None:
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
    assert config.document_sources[0].source_id == "repository"


def test_workspace_config_loads_multi_source_yaml(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "core.yaml"
    config_path.write_text(
        "\n".join(
            [
                "department_id: core",
                "title: Curvature Core",
                f"role_file: {tmp_path / 'core.md'}",
                "sources:",
                f"  curvature: {tmp_path / 'Curvature'}",
                f"  console: {tmp_path / 'curvature-console'}",
                "documents:",
                "  - source: curvature",
                "    path: HANDOFF.md",
                "  - source: console",
                "    path: CURVATURE_CONSOLE_HANDOFF.md",
            ]
        ),
        encoding="utf-8",
    )

    config = load_workspace_config(config_path)

    assert config.source_path("curvature") == tmp_path / "Curvature"
    assert config.source_path("console") == tmp_path / "curvature-console"
    assert [
        (document.source_id, document.relative_path)
        for document in config.document_sources
    ] == [
        ("curvature", Path("HANDOFF.md")),
        ("console", Path("CURVATURE_CONSOLE_HANDOFF.md")),
    ]


def test_workspace_config_rejects_unknown_document_source(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        "\n".join(
            [
                "department_id: core",
                "title: Curvature Core",
                "role_file: role.md",
                "sources:",
                "  curvature: ~/Curvature",
                "documents:",
                "  - source: console",
                "    path: HANDOFF.md",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(WorkspaceConfigError, match="unknown source"):
        load_workspace_config(config_path)


def test_context_loader_reads_role_and_multiple_sources(
    tmp_path: Path,
) -> None:
    curvature = tmp_path / "Curvature"
    console = tmp_path / "curvature-console"
    curvature.mkdir()
    console.mkdir()

    role = console / "CURVATURE_CONSOLE_ROLE_CORE.md"
    role.write_text("Core role", encoding="utf-8")
    (curvature / "HANDOFF.md").write_text(
        "Project state",
        encoding="utf-8",
    )
    (console / "CURVATURE_CONSOLE_HANDOFF.md").write_text(
        "Console state",
        encoding="utf-8",
    )

    config_path = tmp_path / "core.yaml"
    config_path.write_text(
        "\n".join(
            [
                "department_id: core",
                "title: Curvature Core",
                f"role_file: {role}",
                "sources:",
                f"  curvature: {curvature}",
                f"  console: {console}",
                "documents:",
                "  - source: curvature",
                "    path: HANDOFF.md",
                "  - source: console",
                "    path: CURVATURE_CONSOLE_HANDOFF.md",
            ]
        ),
        encoding="utf-8",
    )

    result = WorkspaceContextLoader().load(
        load_workspace_config(config_path)
    )

    assert result.loaded_count == 3
    assert result.errors == ()
    assert [document.label for document in result.documents] == [
        "ROLE",
        "curvature:HANDOFF.md",
        "console:CURVATURE_CONSOLE_HANDOFF.md",
    ]
    assert "Project state" in result.preview_text()
    assert "Console state" in result.preview_text()


def test_context_loader_keeps_repository_boundaries_per_source(
    tmp_path: Path,
) -> None:
    curvature = tmp_path / "Curvature"
    console = tmp_path / "curvature-console"
    curvature.mkdir()
    console.mkdir()

    role = console / "role.md"
    role.write_text("Role", encoding="utf-8")

    config_path = tmp_path / "core.yaml"
    config_path.write_text(
        "\n".join(
            [
                "department_id: core",
                "title: Curvature Core",
                f"role_file: {role}",
                "sources:",
                f"  curvature: {curvature}",
                f"  console: {console}",
                "documents:",
                "  - source: curvature",
                "    path: ../curvature-console/secret.md",
            ]
        ),
        encoding="utf-8",
    )

    result = WorkspaceContextLoader().load(
        load_workspace_config(config_path)
    )

    assert result.loaded_count == 1
    assert len(result.errors) == 1
    assert "escapes repository root" in result.errors[0]


def test_repository_workspaces_use_both_source_roots() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    config_directory = repository_root / "config" / "workspaces"

    expected_roles = {
        "core": "CURVATURE_CONSOLE_ROLE_CORE.md",
        "project": "CURVATURE_CONSOLE_ROLE_PROJECT.md",
        "research": "CURVATURE_CONSOLE_ROLE_RESEARCH.md",
    }

    for department_id in ("project", "core", "research"):
        config = load_workspace_config(
            config_directory / f"{department_id}.yaml"
        )

        assert config.role_file.expanduser() == (
            repository_root / expected_roles[department_id]
        )
        assert config.source_path("console").expanduser() == repository_root
        assert config.source_path("curvature").expanduser() == (
            Path("~/Curvature").expanduser()
        )
        assert {
            document.source_id
            for document in config.document_sources
        } == {"console", "curvature"}
