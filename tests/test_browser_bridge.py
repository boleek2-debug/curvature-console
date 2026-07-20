"""Tests for URL-only shared-project conversation routing."""

from __future__ import annotations

from pathlib import Path

import pytest

from curvature_console.infrastructure.browser_bridge import (
    BOOTSTRAP_CONVERSATION_URLS,
    BrowserBridgeAmbiguousTarget,
    BrowserBridgeConfig,
    BrowserBridgeProcessExited,
    BrowserBridgeRouteUnverified,
    BrowserBridgeStage,
    BrowserExchangeRequest,
    ChatGPTBrowserBridge,
    ChromeLauncher,
    SHARED_PROJECT_NAME,
    SHARED_PROJECT_URL,
)


def _config(tmp_path: Path) -> BrowserBridgeConfig:
    chrome = tmp_path / "google-chrome-stable"
    chrome.write_text("", encoding="utf-8")
    return BrowserBridgeConfig(
        chrome_executable=chrome,
        profile_directory=tmp_path / "profile",
    )


def test_shared_project_identity_is_explicit() -> None:
    assert SHARED_PROJECT_NAME == "Curvature"
    assert SHARED_PROJECT_URL.endswith("/project")


def test_bootstrap_urls_are_per_department_and_title_free() -> None:
    assert set(BOOTSTRAP_CONVERSATION_URLS) == {
        "project",
        "core",
        "research",
    }
    assert all(
        url.startswith("https://chatgpt.com/c/")
        for url in BOOTSTRAP_CONVERSATION_URLS.values()
    )


def test_task_requires_persisted_conversation_url(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    request = BrowserExchangeRequest(
        department_id="core",
        message_text="task",
        create_new_thread=False,
        conversation_url=None,
    )

    with pytest.raises(BrowserBridgeAmbiguousTarget):
        bridge.send_and_receive_hybrid(request)


def test_task_request_uses_existing_conversation() -> None:
    request = BrowserExchangeRequest(
        department_id="core",
        message_text="task",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
    )

    assert request.create_new_thread is False
    assert request.conversation_url.endswith(
        "6a553afb-7878-83ed-b352-99738a964dfe"
    )


def test_handoff_request_does_not_depend_on_chat_title() -> None:
    request = BrowserExchangeRequest(
        department_id="core",
        message_text="handoff",
        create_new_thread=True,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
    )

    assert request.create_new_thread is True


def test_headless_launcher_is_available(tmp_path: Path) -> None:
    command = ChromeLauncher(_config(tmp_path)).command(headless=True)

    assert "--headless=new" in command


def test_bridge_reports_lifecycle_stages(tmp_path: Path) -> None:
    stages: list[BrowserBridgeStage] = []
    bridge = ChatGPTBrowserBridge(_config(tmp_path), stages.append)

    bridge._report_stage(BrowserBridgeStage.CONNECTING)
    bridge._report_stage(BrowserBridgeStage.CLEANING_UP)

    assert stages == [
        BrowserBridgeStage.CONNECTING,
        BrowserBridgeStage.CLEANING_UP,
    ]


def test_owned_process_exit_is_detected_immediately(tmp_path: Path) -> None:
    class ExitedProcess:
        def poll(self):
            return 1

    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    bridge._owned_process = ExitedProcess()

    with pytest.raises(BrowserBridgeProcessExited):
        bridge._assert_browser_alive()


def test_close_terminates_owned_process_and_is_idempotent(
    tmp_path: Path,
) -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.terminated = 0

        def poll(self):
            return None

        def terminate(self) -> None:
            self.terminated += 1

        def wait(self, timeout=None) -> None:
            return None

    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    process = FakeProcess()
    bridge._owned_process = process
    bridge._owned_process_is_headless = True

    bridge.close()
    bridge.close()

    assert process.terminated == 1
    assert bridge._owned_process is None


def test_editor_timeout_is_configurable(tmp_path: Path) -> None:
    config = _config(tmp_path)
    assert config.editor_timeout_seconds == 20.0


def test_route_unverified_preserves_observed_url_and_response() -> None:
    error = BrowserBridgeRouteUnverified(
        observed_url="https://chatgpt.com/g/example",
        response_text="DIAGNOSTIC_RESPONSE",
    )

    assert error.observed_url == "https://chatgpt.com/g/example"
    assert error.response_text == "DIAGNOSTIC_RESPONSE"
    assert "https://chatgpt.com/g/example" in str(error)


def test_global_conversation_url_is_verified(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert bridge._is_conversation_url(
        "https://chatgpt.com/c/6a553afb-7878-83ed-b352-99738a964dfe"
    )


def test_project_scoped_conversation_url_is_verified(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert bridge._is_conversation_url(
        "https://chatgpt.com/g/g-p-6a5ccf24ed988191b1589e5beca5b7c5/"
        "c/6a553afb-7878-83ed-b352-99738a964dfe"
    )


def test_non_conversation_project_url_is_not_verified(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert not bridge._is_conversation_url(
        "https://chatgpt.com/g/g-p-6a5ccf24ed988191b1589e5beca5b7c5/project"
    )


def test_external_conversation_like_url_is_not_verified(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert not bridge._is_conversation_url(
        "https://example.com/c/6a553afb-7878-83ed-b352-99738a964dfe"
    )
