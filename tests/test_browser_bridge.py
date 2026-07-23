"""Tests for deterministic request-bound browser routing."""

from __future__ import annotations

from pathlib import Path

import pytest

from curvature_console.infrastructure.browser_bridge import (
    CapturedDownload,
    BOOTSTRAP_CONVERSATION_URLS,
    SHARED_PROJECT_NAME,
    SHARED_PROJECT_URL,
    BrowserBridgeConfig,
    BrowserBridgeMessageNotConfirmed,
    BrowserBridgeProcessExited,
    BrowserBridgeRouteMismatch,
    BrowserBridgeRouteUnverified,
    BrowserExchangeRequest,
    BrowserExchangeResult,
    ChatGPTBrowserBridge,
    ChromeLauncher,
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


def test_bootstrap_routes_are_conversation_urls() -> None:
    assert set(BOOTSTRAP_CONVERSATION_URLS) == {
        "project",
        "core",
        "research",
    }
    assert all(
        value.startswith("https://chatgpt.com/c/")
        for value in BOOTSTRAP_CONVERSATION_URLS.values()
    )


def test_request_requires_request_id(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    request = BrowserExchangeRequest(
        request_id="",
        department_id="core",
        message_text="task",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
    )

    with pytest.raises(ValueError, match="Request id"):
        bridge._validate_request(request)


def test_request_and_result_preserve_request_identity() -> None:
    request = BrowserExchangeRequest(
        request_id="request-123",
        department_id="core",
        message_text="task",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
    )
    result = BrowserExchangeResult(
        request_id=request.request_id,
        department_id=request.department_id,
        project_name=SHARED_PROJECT_NAME,
        project_url=SHARED_PROJECT_URL,
        conversation_url=request.conversation_url or "",
        response_text="response",
    )

    assert result.request_id == "request-123"
    assert result.department_id == "core"


def test_bridge_does_not_expose_active_page_selection(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert not hasattr(bridge, "active_page")
    assert hasattr(bridge, "open_dedicated_page")


def test_route_verification_uses_conversation_id(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    bridge._verify_requested_route(
        "https://chatgpt.com/c/core-id",
        "https://chatgpt.com/g/project-id/c/core-id",
    )


def test_route_mismatch_is_rejected(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    with pytest.raises(BrowserBridgeRouteMismatch):
        bridge._verify_requested_route(
            "https://chatgpt.com/c/core-id",
            "https://chatgpt.com/g/project-id/c/research-id",
        )


def test_global_and_project_scoped_routes_are_verified(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert bridge._is_conversation_url(
        "https://chatgpt.com/c/core-id"
    )
    assert bridge._is_conversation_url(
        "https://chatgpt.com/g/project-id/c/core-id"
    )
    assert not bridge._is_conversation_url(
        "https://chatgpt.com/g/project-id/project"
    )
    assert not bridge._is_conversation_url(
        "https://example.com/c/core-id"
    )


def test_message_normalisation_preserves_internal_lines(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert bridge._normalize_message_text(" a  \n\n b \n") == "a\n\n b"


def test_new_wrong_user_message_is_rejected(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(
        BrowserBridgeConfig(
            chrome_executable=_config(tmp_path).chrome_executable,
            profile_directory=tmp_path / "profile",
            message_confirmation_timeout_seconds=0.01,
            response_poll_interval_seconds=0.001,
        )
    )

    class FakeMessage:
        def inner_text(self):
            return "wrong request"

    class FakeMessages:
        def count(self):
            return 1

        def nth(self, index):
            assert index == 0
            return FakeMessage()

    class FakePage:
        def locator(self, selector):
            assert selector == '[data-message-author-role="user"]'
            return FakeMessages()

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None

    with pytest.raises(BrowserBridgeMessageNotConfirmed):
        bridge._wait_for_confirmed_user_message(
            page=FakePage(),
            baseline_count=0,
            request_id="expected-request",
        )


def test_owned_page_is_closed_without_closing_external_browser(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakePage:
        def __init__(self):
            self.closed = 0

        def is_closed(self):
            return False

        def close(self):
            self.closed += 1

    page = FakePage()
    bridge._dedicated_page = page
    bridge._close_dedicated_page()

    assert page.closed == 1
    assert bridge._dedicated_page is None


def test_process_exit_is_detected(tmp_path: Path) -> None:
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

    bridge.close()
    bridge.close()

    assert process.terminated == 1
    assert bridge._owned_process is None


def test_headless_launcher_is_available(tmp_path: Path) -> None:
    command = ChromeLauncher(_config(tmp_path)).command(headless=True)

    assert "--headless=new" in command


def test_route_unverified_preserves_observed_url_and_response() -> None:
    error = BrowserBridgeRouteUnverified(
        observed_url="https://chatgpt.com/g/example",
        response_text="DIAGNOSTIC_RESPONSE",
    )

    assert error.observed_url == "https://chatgpt.com/g/example"
    assert error.response_text == "DIAGNOSTIC_RESPONSE"


def test_transport_message_contains_request_marker(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    request = BrowserExchangeRequest(
        request_id="request-abc",
        department_id="core",
        message_text="Task package body",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
    )

    transport = bridge._transport_message_text(request)

    assert transport.startswith("CURVATURE_REQUEST_ID: request-abc\n\n")
    assert transport.endswith("Task package body\n")


def test_matching_request_marker_confirms_user_message(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeMessage:
        def inner_text(self):
            return (
                "CURVATURE_REQUEST_ID: request-abc\n\n"
                "Rendered Markdown may differ."
            )

    class FakeMessages:
        def count(self):
            return 1

        def nth(self, index):
            assert index == 0
            return FakeMessage()

    class FakePage:
        def locator(self, selector):
            assert selector == '[data-message-author-role="user"]'
            return FakeMessages()

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None

    bridge._wait_for_confirmed_user_message(
        page=FakePage(),
        baseline_count=0,
        request_id="request-abc",
    )


def test_generated_file_link_detection(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert bridge._is_generated_file_link(
        "sandbox:/mnt/data/result.zip",
        None,
    )
    assert bridge._is_generated_file_link(
        "https://chatgpt.com/backend/file",
        "result.zip",
    )
    assert bridge._is_generated_file_link(
        "https://chatgpt.com/backend-api/files/file-123",
        None,
    )
    assert bridge._is_generated_file_link(
        "https://chatgpt.com/backend-api/estuary/content?id=file-123",
        None,
    )
    assert bridge._is_generated_file_link(
        "https://files.oaiusercontent.com/file-123/result.zip",
        None,
    )
    assert bridge._is_generated_file_link(
        "https://chatgpt.com/opaque-link",
        None,
        "Download result.zip",
    )
    assert not bridge._is_generated_file_link(
        "https://example.com/report",
        None,
        "Read report",
    )


def test_collision_safe_download_path_preserves_original_name(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "package.zip").write_bytes(b"first")
    (inbox / "package (2).zip").write_bytes(b"second")

    target = bridge._collision_safe_path(inbox, "package.zip")

    assert target == inbox / "package (3).zip"


def test_collision_safe_download_path_removes_directory_components(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    target = bridge._collision_safe_path(inbox, "../../unsafe.txt")

    assert target == inbox / "unsafe.txt"


def test_route_unverified_preserves_captured_downloads(
    tmp_path: Path,
) -> None:
    download = CapturedDownload(
        original_filename="result.zip",
        saved_path=tmp_path / "result.zip",
        source_url="https://example.test/result.zip",
    )

    error = BrowserBridgeRouteUnverified(
        observed_url="chrome-error://chromewebdata/",
        response_text="Download result.zip",
        downloads=(download,),
    )

    assert error.downloads == (download,)
