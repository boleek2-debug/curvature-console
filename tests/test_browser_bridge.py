"""Tests for deterministic request-bound browser routing."""

from __future__ import annotations

from pathlib import Path
import signal

import pytest

from curvature_console.infrastructure.browser_bridge import (
    BOOTSTRAP_CONVERSATION_URLS,
    SHARED_PROJECT_NAME,
    SHARED_PROJECT_URL,
    BrowserBridgeConfig,
    BrowserBridgeEditorUnavailable,
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
    xvfb_run = tmp_path / "xvfb-run"
    xvfb_run.write_text("", encoding="utf-8")
    return BrowserBridgeConfig(
        chrome_executable=chrome,
        profile_directory=tmp_path / "profile",
        xvfb_run_executable=xvfb_run,
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
            expected_text="expected request",
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


def test_close_terminates_owned_process_group_and_is_idempotent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.pid = 4321
            self.wait_calls = 0

        def poll(self):
            return None

        def wait(self, timeout=None) -> None:
            self.wait_calls += 1

    signals = []
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    process = FakeProcess()
    bridge._owned_process = process
    bridge._owned_process_group_id = process.pid

    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.os.killpg",
        lambda pgid, signal_number: signals.append(
            (pgid, signal_number)
        ),
    )
    monkeypatch.setattr(
        bridge,
        "_wait_for_cdp_release",
        lambda timeout: True,
    )

    bridge.close()
    bridge.close()

    assert signals == [(4321, signal.SIGTERM)]
    assert process.wait_calls == 1
    assert bridge._owned_process is None
    assert bridge._owned_process_group_id is None


def test_cleanup_kills_group_when_wrapper_already_exited(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class ExitedWrapper:
        pid = 9876

        def poll(self):
            return 0

    signals = []
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    bridge._owned_process = ExitedWrapper()
    bridge._owned_process_group_id = 9876
    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.os.killpg",
        lambda pgid, signal_number: signals.append(
            (pgid, signal_number)
        ),
    )
    monkeypatch.setattr(
        bridge,
        "_wait_for_cdp_release",
        lambda timeout: True,
    )

    bridge._terminate_owned_process()

    assert signals == [(9876, signal.SIGTERM)]


def test_cleanup_escalates_when_cdp_port_stays_open(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeProcess:
        pid = 2468

        def poll(self):
            return 0

    signals = []
    release_results = iter((False, True))
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    bridge._owned_process = FakeProcess()
    bridge._owned_process_group_id = 2468

    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.os.killpg",
        lambda pgid, signal_number: signals.append(
            (pgid, signal_number)
        ),
    )
    monkeypatch.setattr(
        bridge,
        "_wait_for_cdp_release",
        lambda timeout: next(release_results),
    )

    bridge._terminate_owned_process()

    assert signals == [
        (2468, signal.SIGTERM),
        (2468, signal.SIGKILL),
    ]


def test_background_launcher_uses_xvfb_not_chromium_headless(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    command = ChromeLauncher(config).command(headless=True)

    assert command[0] == str(config.xvfb_run_executable)
    assert "--auto-servernum" in command
    assert "--headless=new" not in command
    assert str(config.chrome_executable) in command


def test_route_unverified_preserves_observed_url_and_response() -> None:
    error = BrowserBridgeRouteUnverified(
        observed_url="https://chatgpt.com/g/example",
        response_text="DIAGNOSTIC_RESPONSE",
    )

    assert error.observed_url == "https://chatgpt.com/g/example"
    assert error.response_text == "DIAGNOSTIC_RESPONSE"


def test_user_message_confirmation_accepts_unique_request_marker(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeMessage:
        def inner_text(self):
            return (
                "CURVATURE_REQUEST_ID: request-123\n"
                "Rendered heading\nRendered list item"
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
        expected_text="# Raw heading\n\n- Raw list item",
        confirmation_marker="CURVATURE_REQUEST_ID: request-123",
    )


def test_user_message_confirmation_rejects_foreign_request_marker(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeMessage:
        def inner_text(self):
            return "CURVATURE_REQUEST_ID: another-request"

    class FakeMessages:
        def count(self):
            return 1

        def nth(self, index):
            assert index == 0
            return FakeMessage()

    class FakePage:
        def locator(self, selector):
            return FakeMessages()

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None

    with pytest.raises(
        BrowserBridgeMessageNotConfirmed,
        match="did not contain the current request marker",
    ):
        bridge._wait_for_confirmed_user_message(
            page=FakePage(),
            baseline_count=0,
            expected_text="task",
            confirmation_marker="CURVATURE_REQUEST_ID: request-123",
        )


def test_editor_unavailable_does_not_trigger_visible_fallback(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    request = BrowserExchangeRequest(
        request_id="request-editor-unavailable",
        department_id="core",
        message_text="task",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
    )
    bridge.connect_or_launch_hybrid = lambda: None
    bridge._send_and_receive_once = lambda request: (_ for _ in ()).throw(
        BrowserBridgeEditorUnavailable("missing editor")
    )
    bridge._switch_to_visible_browser = lambda: pytest.fail(
        "Visible Chrome must not be launched for editor unavailability."
    )

    with pytest.raises(BrowserBridgeEditorUnavailable):
        bridge.send_and_receive_hybrid(request)


def test_runtime_log_configuration_creates_timestamped_file(
    tmp_path: Path,
) -> None:
    from curvature_console.infrastructure.runtime_logging import (
        configure_runtime_logging,
        get_runtime_logger,
    )

    log_path = configure_runtime_logging(tmp_path)
    get_runtime_logger("test").warning("diagnostic line")

    assert log_path.parent == tmp_path / "logs"
    assert log_path.name.startswith("console-")
    assert log_path.suffix == ".log"
    assert "diagnostic line" in log_path.read_text(encoding="utf-8")


def test_cloudflare_just_a_moment_title_is_human_verification(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class EmptyBody:
        def count(self):
            return 0

    class FakePage:
        def title(self):
            return "Just a moment..."

        def locator(self, selector):
            assert selector == "body"
            return EmptyBody()

    assert bridge._human_verification_is_visible(FakePage()) is True


def test_success_logging_accepts_result_without_downloads(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    request = BrowserExchangeRequest(
        request_id="request-no-download-field",
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
        response_text="CORE_XVFB_OK",
    )

    bridge.connect_or_launch_hybrid = lambda: None
    bridge._send_and_receive_once = lambda request: result

    assert bridge.send_and_receive_hybrid(request) == result
