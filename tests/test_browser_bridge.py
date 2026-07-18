"""Tests for ASSISTANT-001B5.2A browser bridge foundation."""

from __future__ import annotations

from pathlib import Path

import pytest

from curvature_console.infrastructure.browser_bridge import (
    BrowserBridgeConfig,
    ChatGPTBrowserBridge,
    ChromeLauncher,
    DEPARTMENT_PROJECT_NAMES,
)


def test_default_config_uses_local_runtime_profile(tmp_path: Path) -> None:
    config = BrowserBridgeConfig.default(tmp_path)

    assert config.chrome_executable == Path(
        "/usr/bin/google-chrome-stable"
    )
    assert config.profile_directory == (
        tmp_path / "data" / "browser-profile"
    )
    assert config.cdp_url == "http://127.0.0.1:9222"


def test_launcher_builds_expected_chrome_command(tmp_path: Path) -> None:
    chrome = tmp_path / "google-chrome-stable"
    chrome.write_text("", encoding="utf-8")
    config = BrowserBridgeConfig(
        chrome_executable=chrome,
        profile_directory=tmp_path / "profile",
        debugging_port=9333,
    )

    command = ChromeLauncher(config).command()

    assert command[0] == str(chrome)
    assert "--remote-debugging-port=9333" in command
    assert (
        f"--user-data-dir={tmp_path / 'profile'}"
        in command
    )
    assert command[-1] == "https://chatgpt.com"
    assert config.profile_directory.is_dir()


def test_invalid_debugging_port_is_rejected(tmp_path: Path) -> None:
    chrome = tmp_path / "chrome"
    chrome.write_text("", encoding="utf-8")
    config = BrowserBridgeConfig(
        chrome_executable=chrome,
        profile_directory=tmp_path / "profile",
        debugging_port=0,
    )

    with pytest.raises(ValueError, match="Debugging port"):
        config.validate()


def test_department_project_mapping_is_explicit() -> None:
    assert DEPARTMENT_PROJECT_NAMES == {
        "project": "Curvature Project",
        "core": "Curvature Core",
        "research": "Curvature Research",
    }


def test_unknown_department_is_rejected(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(
        BrowserBridgeConfig(
            chrome_executable=tmp_path / "chrome",
            profile_directory=tmp_path / "profile",
        )
    )

    with pytest.raises(ValueError, match="Unknown department"):
        bridge.project_name_for_department("unknown")


def test_active_page_requires_connection(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(
        BrowserBridgeConfig(
            chrome_executable=tmp_path / "chrome",
            profile_directory=tmp_path / "profile",
        )
    )

    with pytest.raises(RuntimeError, match="not connected"):
        bridge.active_page()
