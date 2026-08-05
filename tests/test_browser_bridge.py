"""Tests for deterministic request-bound browser routing."""

from __future__ import annotations

from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import signal

import pytest

from curvature_console.infrastructure.browser_bridge import (
    BOOTSTRAP_CONVERSATION_URLS,
    SHARED_PROJECT_NAME,
    SHARED_PROJECT_URL,
    BrowserBridgeCancelled,
    BrowserBridgeConfig,
    BrowserBridgeEditorUnavailable,
    BrowserBridgeError,
    BrowserBridgeMessageNotConfirmed,
    BrowserBridgeMessageNotReady,
    BrowserBridgeProcessExited,
    BrowserBridgeRouteMismatch,
    BrowserBridgeRouteUnverified,
    BrowserExchangeRequest,
    BrowserExchangeResult,
    ChatGPTBrowserBridge,
    _ResponseBackedDownload,
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


def test_safe_download_filename_preserves_real_extension(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert bridge._safe_download_filename("../../report.txt") == "report.txt"
    assert bridge._safe_download_filename("notes.md") == "notes.md"
    assert bridge._safe_download_filename("data.csv") == "data.csv"
    assert bridge._safe_download_filename("archive.zip") == "archive.zip"


def test_collision_safe_path_preserves_extension(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    existing = tmp_path / "report.txt"
    existing.write_text("first", encoding="utf-8")

    assert bridge._collision_safe_path(
        tmp_path,
        "report.txt",
    ) == tmp_path / "report-2.txt"


def test_generated_file_link_detection_is_format_agnostic(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    assert bridge._is_generated_file_link(
        "sandbox:/mnt/data/result.txt",
        None,
    )
    assert bridge._is_generated_file_link(
        "https://files.oaiusercontent.com/file.pdf",
        None,
    )
    assert bridge._is_generated_file_link(
        "https://example.com/download",
        "result.json",
    )
    assert not bridge._is_generated_file_link(
        "https://example.com/article",
        None,
    )


def test_exchange_result_defaults_to_no_downloads() -> None:
    result = BrowserExchangeResult(
        request_id="request",
        department_id="core",
        project_name=SHARED_PROJECT_NAME,
        project_url=SHARED_PROJECT_URL,
        conversation_url="https://chatgpt.com/c/core",
        response_text="done",
    )

    assert result.downloaded_files == ()


def test_file_card_candidate_is_detected_without_anchor(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def get_attribute(self, name):
            return {
                "aria-label": "Download curvature-download-test.txt",
                "title": None,
                "data-testid": "file-download-button",
            }.get(name)

        def inner_text(self):
            return "curvature-download-test.txt"

    assert bridge._is_generated_file_candidate(
        FakeCandidate(),
        "",
        None,
    )


def test_filename_can_be_read_from_file_card_text(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def get_attribute(self, name):
            return None

        def inner_text(self):
            return "Download curvature-download-test.txt"

    assert bridge._filename_from_candidate(
        FakeCandidate()
    ) == "curvature-download-test.txt"


def test_filename_extraction_does_not_include_action_label(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def get_attribute(self, name):
            return None

        def inner_text(self):
            return "Download curvature-download-test.txt"

    assert (
        bridge._filename_from_candidate(FakeCandidate())
        == "curvature-download-test.txt"
    )


def test_filename_extraction_preserves_spaces_inside_filename(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def get_attribute(self, name):
            return None

        def inner_text(self):
            return "Download curvature report 2026.txt"

    assert (
        bridge._filename_from_candidate(FakeCandidate())
        == "curvature report 2026.txt"
    )


def test_filename_extraction_strips_common_action_prefixes(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def __init__(self, text):
            self._text = text

        def get_attribute(self, name):
            return None

        def inner_text(self):
            return self._text

    assert (
        bridge._filename_from_candidate(
            FakeCandidate("Open: curvature report 2026.txt")
        )
        == "curvature report 2026.txt"
    )
    assert (
        bridge._filename_from_candidate(
            FakeCandidate("Save - result.json")
        )
        == "result.json"
    )


def test_dom_snapshot_diff_reports_active_layer(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    before = {
        "body": {"style": "", "dataScrollLocked": None},
        "activeElement": {"tag": "div"},
        "closeButton": None,
        "layer": None,
        "layerControls": [],
        "activeAncestors": [],
    }
    after = {
        "body": {
            "style": "pointer-events: none;",
            "dataScrollLocked": "1",
        },
        "activeElement": {"tag": "button", "text": "Close"},
        "closeButton": {"tag": "button", "text": "Close"},
        "layer": {"tag": "div", "text": "Generated file details"},
        "layerControls": [
            {"tag": "button", "text": "Download"},
        ],
        "activeAncestors": [
            {"tag": "button", "text": "Close"},
            {"tag": "div", "text": "Generated file details"},
        ],
    }

    changes = bridge._diff_interaction_snapshots(before, after)

    assert changes["bodyChanged"] is True
    assert changes["activeElementChanged"] is True
    assert changes["closeButtonAppeared"] is True
    assert changes["layerAppeared"] is True
    assert changes["afterLayerControls"] == [
        {"tag": "button", "text": "Download"},
    ]


def test_observe_file_activation_channels_collects_browser_events(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class EventItem:
        method = "GET"
        url = "https://example.test/file"
        resource_type = "fetch"
        status = 200
        headers = {
            "content-type": "text/plain",
            "content-disposition": "attachment; filename=test.txt",
        }
        suggested_filename = "test.txt"
        type = "log"
        text = "console"

    class FakeCandidate:
        def __init__(self):
            self.scrolled = False
            self.clicked = False

        def scroll_into_view_if_needed(self):
            self.scrolled = True

        def click(self):
            self.clicked = True

    class FakePage:
        def __init__(self):
            self.handlers = {}
            self.init_script = None
            self.waited = None

        def on(self, name, handler):
            self.handlers[name] = handler

        def add_init_script(self, script):
            self.init_script = script

        def wait_for_timeout(self, value):
            self.waited = value

        def evaluate(self, script):
            return {
                "fetches": [{"url": "https://example.test/file"}],
                "xhrs": [],
                "objectUrls": [{"url": "blob:test", "size": 3}],
                "anchorClicks": [{"href": "blob:test", "download": "test.txt"}],
            }

    page = FakePage()
    candidate = FakeCandidate()
    request = BrowserExchangeRequest(
        request_id="request",
        department_id="core",
        message_text="observe file",
        create_new_thread=False,
        conversation_url="https://chatgpt.com/c/core",
    )

    result = bridge._observe_file_activation_channels(
        page=page,
        candidate=candidate,
        request=request,
        candidate_index=0,
    )

    assert candidate.scrolled is True
    assert candidate.clicked is True
    assert page.waited == 2000
    assert "window.fetch" in page.init_script
    assert "URL.createObjectURL" in page.init_script
    assert result["browser"]["objectUrls"][0]["url"] == "blob:test"


def test_response_backed_download_saves_bytes(tmp_path: Path) -> None:
    download = _ResponseBackedDownload(
        suggested_filename="file.txt",
        body_bytes=b"payload",
        source_url="https://chatgpt.com/backend-api/estuary/content",
    )
    target = tmp_path / "file.txt"

    download.save_as(target)

    assert target.read_bytes() == b"payload"


def test_trigger_candidate_download_captures_attachment_fetch_response(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeResponse:
        status = 200
        url = "https://chatgpt.com/backend-api/estuary/content?id=file"
        headers = {
            "content-disposition": 'attachment; filename="file.txt"',
            "content-type": "text/plain",
        }

        def body(self):
            return b"CURVATURE_DOWNLOAD_CAPTURE_OK"

    class FakeDownloadInfo:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            raise PlaywrightTimeoutError("no native download")

    class FakePage:
        def __init__(self):
            self.handler = None

        def on(self, name, handler):
            assert name == "response"
            self.handler = handler

        def remove_listener(self, name, handler):
            assert name == "response"
            assert handler is self.handler

        def expect_download(self, timeout):
            return FakeDownloadInfo()

        def wait_for_timeout(self, milliseconds):
            assert milliseconds == 250

    class FakeCandidate:
        def scroll_into_view_if_needed(self):
            return None

        def click(self):
            page.handler(FakeResponse())

        def get_attribute(self, name):
            if name == "aria-label":
                return "curvature-download-test.txt"
            return None

        def inner_text(self):
            return "curvature-download-test.txt"

        def evaluate(self, script):
            if script == "(element) => element.tagName":
                return "BUTTON"
            raise AssertionError(script)

    page = FakePage()
    result = bridge._trigger_candidate_download(
        page=page,
        candidate=FakeCandidate(),
        request=BrowserExchangeRequest(
            request_id="request",
            department_id="core",
            message_text="create file",
            create_new_thread=False,
            conversation_url="https://chatgpt.com/c/core",
        ),
        candidate_index=0,
    )

    assert result.suggested_filename == "curvature-download-test.txt"
    assert result.body_bytes == b"CURVATURE_DOWNLOAD_CAPTURE_OK"


def test_trigger_candidate_download_uses_fallback_activation_methods(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeDownloadInfo:
        def __init__(self, succeeds):
            self.succeeds = succeeds
            self.value = "download"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            if not self.succeeds:
                raise PlaywrightTimeoutError("no download")
            return False

    class FakeMouse:
        def __init__(self):
            self.clicked = False

        def click(self, x, y):
            self.clicked = (x, y)

    class FakePage:
        def __init__(self):
            self.calls = 0
            self.mouse = FakeMouse()
            self.response_handler = None

        def on(self, name, handler):
            assert name == "response"
            self.response_handler = handler

        def remove_listener(self, name, handler):
            assert name == "response"
            assert handler is self.response_handler
            self.response_handler = None

        def wait_for_timeout(self, milliseconds):
            assert milliseconds == 250

        def expect_download(self, timeout):
            self.calls += 1
            return FakeDownloadInfo(self.calls == 2)

    class FakeCandidate:
        def __init__(self):
            self.scrolled = False
            self.clicked = False

        def scroll_into_view_if_needed(self):
            self.scrolled = True

        def click(self):
            self.clicked = True

        def bounding_box(self):
            return {"x": 10, "y": 20, "width": 30, "height": 40}

        def press(self, key):
            raise AssertionError("keyboard fallback should not be reached")

        def evaluate(self, script):
            if script == "(element) => element.tagName":
                return "BUTTON"
            raise AssertionError("pointer fallback should not be reached")

        def get_attribute(self, name):
            if name == "aria-label":
                return "curvature-download-test.txt"
            return None

        def inner_text(self):
            return "curvature-download-test.txt"

    page = FakePage()
    candidate = FakeCandidate()

    result = bridge._trigger_candidate_download(
        page=page,
        candidate=candidate,
        request=BrowserExchangeRequest(
            request_id="request",
            department_id="core",
            message_text="create file",
            create_new_thread=False,
            conversation_url="https://chatgpt.com/c/core",
        ),
        candidate_index=0,
    )

    assert result == "download"
    assert candidate.scrolled is True
    assert candidate.clicked is True
    assert page.mouse.clicked == (25.0, 40.0)


def test_dispatch_candidate_pointer_sequence_uses_dom_events(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def __init__(self):
            self.script = None

        def evaluate(self, script):
            self.script = script

    candidate = FakeCandidate()
    bridge._dispatch_candidate_pointer_sequence(candidate)

    assert "PointerEvent" in candidate.script
    assert 'new MouseEvent("click"' in candidate.script


def test_coding_citation_is_not_treated_as_generated_file_candidate(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def get_attribute(self, name):
            return {
                "aria-label": "Coding Citation",
                "title": None,
                "data-testid": None,
            }.get(name)

        def inner_text(self):
            return ""

    assert not bridge._is_generated_file_candidate(
        FakeCandidate(),
        "",
        None,
    )


def test_contenteditable_editor_uses_keyboard_insert_text(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeKeyboard:
        def __init__(self) -> None:
            self.pressed: list[str] = []
            self.inserted: list[str] = []

        def press(self, key: str) -> None:
            self.pressed.append(key)

        def insert_text(self, text: str) -> None:
            self.inserted.append(text)

    class FakePage:
        def __init__(self) -> None:
            self.keyboard = FakeKeyboard()

    class FakeEditor:
        def __init__(self) -> None:
            self.click_calls: list[int] = []
            self.fill_calls: list[tuple[str, int]] = []

        def get_attribute(self, name: str) -> str | None:
            assert name == "contenteditable"
            return "true"

        def click(self, timeout: int) -> None:
            self.click_calls.append(timeout)

        def fill(self, text: str, timeout: int) -> None:
            self.fill_calls.append((text, timeout))

    page = FakePage()
    editor = FakeEditor()

    bridge._enter_message_text(
        page=page,
        editor=editor,
        message_text="large transfer package",
    )

    assert editor.fill_calls == []
    assert editor.click_calls == [
        int(bridge.config.editor_timeout_seconds * 1000)
    ]
    assert page.keyboard.pressed == ["Control+A", "Backspace"]
    assert page.keyboard.inserted == ["large transfer package"]


def test_non_contenteditable_editor_uses_locator_fill(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakePage:
        keyboard = object()

    class FakeEditor:
        def __init__(self) -> None:
            self.fill_calls: list[tuple[str, int]] = []

        def get_attribute(self, name: str) -> str | None:
            assert name == "contenteditable"
            return None

        def fill(self, text: str, timeout: int) -> None:
            self.fill_calls.append((text, timeout))

    editor = FakeEditor()

    bridge._enter_message_text(
        page=FakePage(),
        editor=editor,
        message_text="ordinary textarea message",
    )

    assert editor.fill_calls == [
        (
            "ordinary textarea message",
            int(bridge.config.editor_timeout_seconds * 1000),
        )
    ]


def test_submit_message_clicks_enabled_send_button(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeButton:
        def __init__(self) -> None:
            self.clicks = 0

        def is_visible(self):
            return True

        def is_enabled(self):
            return True

        def click(self, timeout=None):
            assert timeout == int(bridge.config.editor_timeout_seconds * 1000)
            self.clicks += 1

    class FakeLocator:
        def __init__(self, button=None) -> None:
            self.button = button

        def count(self):
            return 1 if self.button is not None else 0

        def nth(self, index):
            assert index == 0
            return self.button

    class FakeKeyboard:
        def press(self, key):
            raise AssertionError("Enter fallback must not be used")

    class FakePage:
        def __init__(self, button) -> None:
            self.button = button
            self.keyboard = FakeKeyboard()

        def locator(self, selector):
            if selector == 'button[data-testid="send-button"]':
                return FakeLocator(self.button)
            return FakeLocator()

    class FakeEditor:
        pass

    button = FakeButton()
    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None

    bridge._wait_for_submission_effect = lambda **kwargs: True
    method = bridge._submit_message(
        page=FakePage(button),
        editor=FakeEditor(),
        baseline_user_count=3,
    )

    assert method == "send_button"
    assert button.clicks == 1


def test_submit_message_uses_enter_only_when_send_button_is_unavailable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bridge = ChatGPTBrowserBridge(
        BrowserBridgeConfig(
            chrome_executable=_config(tmp_path).chrome_executable,
            profile_directory=tmp_path / "profile",
            editor_timeout_seconds=0.01,
        )
    )

    class FakeLocator:
        def count(self):
            return 0

    class FakeKeyboard:
        def __init__(self) -> None:
            self.keys = []

        def press(self, key):
            self.keys.append(key)

    class FakePage:
        def __init__(self) -> None:
            self.keyboard = FakeKeyboard()

        def locator(self, selector):
            return FakeLocator()

    class FakeEditor:
        def __init__(self) -> None:
            self.clicks = 0

        def click(self, timeout=None):
            self.clicks += 1

    page = FakePage()
    editor = FakeEditor()
    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.time.sleep",
        lambda seconds: None,
    )

    bridge._wait_for_submission_effect = lambda **kwargs: True
    method = bridge._submit_message(
        page=page,
        editor=editor,
        baseline_user_count=2,
    )

    assert method == "keyboard_enter"
    assert page.keyboard.keys == ["Enter"]
    assert editor.clicks == 1


def test_submit_message_falls_back_to_enter_when_send_click_has_no_effect(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeButton:
        def is_visible(self):
            return True

        def is_enabled(self):
            return True

        def click(self, timeout=None):
            return None

    class FakeLocator:
        def __init__(self, button=None) -> None:
            self.button = button

        def count(self):
            return 1 if self.button is not None else 0

        def nth(self, index):
            return self.button

    class FakeKeyboard:
        def __init__(self) -> None:
            self.keys = []

        def press(self, key):
            self.keys.append(key)

    class FakePage:
        def __init__(self) -> None:
            self.keyboard = FakeKeyboard()

        def locator(self, selector):
            if selector == 'button[data-testid="send-button"]':
                return FakeLocator(FakeButton())
            return FakeLocator()

    class FakeEditor:
        def __init__(self) -> None:
            self.clicks = 0

        def click(self, timeout=None):
            self.clicks += 1

    effects = iter((False, True))
    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    bridge._wait_for_submission_effect = lambda **kwargs: next(effects)

    page = FakePage()
    editor = FakeEditor()
    method = bridge._submit_message(
        page=page,
        editor=editor,
        baseline_user_count=8,
    )

    assert method == "send_button_then_keyboard_enter"
    assert page.keyboard.keys == ["Enter"]
    assert editor.clicks == 1


def test_user_message_confirmation_scans_marker_when_count_is_unchanged(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeMessage:
        def __init__(self, text: str) -> None:
            self._text = text

        def inner_text(self):
            return self._text

    class FakeMessages:
        def __init__(self) -> None:
            self._messages = [
                FakeMessage("older rendered request"),
                FakeMessage("CURVATURE_REQUEST_ID: request-virtualised"),
            ]

        def count(self):
            return 2

        def nth(self, index):
            return self._messages[index]

    class FakePage:
        def locator(self, selector):
            assert selector == '[data-message-author-role="user"]'
            return FakeMessages()

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None

    bridge._wait_for_confirmed_user_message(
        page=FakePage(),
        baseline_count=2,
        expected_text="task",
        confirmation_marker=(
            "CURVATURE_REQUEST_ID: request-virtualised"
        ),
    )


def test_user_message_confirmation_accepts_new_assistant_turn(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeMessages:
        def count(self):
            return 2

        def nth(self, index):
            raise AssertionError("No user message scan should be required")

    class FakeAssistantMessages:
        def count(self):
            return 4

    class FakePage:
        def locator(self, selector):
            if selector == '[data-message-author-role="user"]':
                return FakeMessages()
            assert selector == '[data-message-author-role="assistant"]'
            return FakeAssistantMessages()

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None

    bridge._wait_for_confirmed_user_message(
        page=FakePage(),
        baseline_count=2,
        baseline_assistant_count=3,
        expected_text="task",
        confirmation_marker="CURVATURE_REQUEST_ID: request-assistant-proof",
    )


def test_completed_response_accepts_new_message_id_when_count_is_unchanged(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeMessage:
        def __init__(self, message_id: str, text: str) -> None:
            self.message_id = message_id
            self.text = text

        def get_attribute(self, name):
            assert name == "data-message-id"
            return self.message_id

        def inner_text(self):
            return self.text

    class FakeMessages:
        def __init__(self) -> None:
            self.messages = [
                FakeMessage("assistant-old-1", "Older response"),
                FakeMessage("assistant-new-2", "B5.5D1-H3 DELIVERY RECEIVED"),
            ]

        def count(self):
            return len(self.messages)

        def nth(self, index):
            return self.messages[index]

    class FakePage:
        def locator(self, selector):
            assert selector == '[data-message-author-role="assistant"]'
            return FakeMessages()

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    bridge._generation_is_active = lambda page: False

    result = bridge._wait_for_completed_response(
        page=FakePage(),
        baseline_count=2,
        baseline_signatures=(
            ("assistant-old-1", "Older response"),
            ("assistant-old-2", "Previous response"),
        ),
    )

    assert result == ("B5.5D1-H3 DELIVERY RECEIVED", "assistant-new-2")


def test_assistant_message_signatures_capture_id_and_normalized_text(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeMessage:
        def __init__(self, message_id: str, text: str) -> None:
            self.message_id = message_id
            self.text = text

        def get_attribute(self, name):
            assert name == "data-message-id"
            return self.message_id

        def inner_text(self):
            return self.text

    class FakeMessages:
        def count(self):
            return 2

        def nth(self, index):
            return (
                FakeMessage("assistant-1", " First\nresponse ")
                if index == 0
                else FakeMessage("assistant-2", "Second   response")
            )

    class FakePage:
        def locator(self, selector):
            assert selector == '[data-message-author-role="assistant"]'
            return FakeMessages()

    assert bridge._assistant_message_signatures(FakePage()) == (
        ("assistant-1", "First\nresponse"),
        ("assistant-2", "Second   response"),
    )


def test_large_contenteditable_editor_uses_verified_clipboard_paste(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    message = "large package\n" * 500

    class FakeContext:
        def __init__(self) -> None:
            self.permissions = []

        def grant_permissions(self, permissions, origin):
            self.permissions.append((permissions, origin))

    class FakeKeyboard:
        def __init__(self, editor) -> None:
            self.editor = editor
            self.pressed: list[str] = []
            self.inserted: list[str] = []

        def press(self, key: str) -> None:
            self.pressed.append(key)
            if key == "Control+V":
                self.editor.text = message

        def insert_text(self, text: str) -> None:
            self.inserted.append(text)

    class FakeEditor:
        def __init__(self) -> None:
            self.text = ""

        def get_attribute(self, name: str) -> str | None:
            assert name == "contenteditable"
            return "true"

        def click(self, timeout: int) -> None:
            return None

        def inner_text(self) -> str:
            return self.text

    editor = FakeEditor()

    class FakePage:
        def __init__(self) -> None:
            self.context = FakeContext()
            self.keyboard = FakeKeyboard(editor)
            self.clipboard_text = ""

        def evaluate(self, script: str, text: str) -> bool:
            assert "navigator.clipboard.writeText" in script
            self.clipboard_text = text
            return True

    page = FakePage()
    bridge._enter_message_text(
        page=page,
        editor=editor,
        message_text=message,
    )

    assert page.clipboard_text == message
    assert page.context.permissions == [
        (["clipboard-read", "clipboard-write"], "https://chatgpt.com")
    ]
    assert page.keyboard.inserted == []
    assert page.keyboard.pressed == ["Control+A", "Backspace", "Control+V"]


def test_large_contenteditable_editor_falls_back_when_all_fast_paths_fail(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    message = "large package\n" * 500

    class FakeContext:
        def grant_permissions(self, permissions, origin):
            raise RuntimeError("clipboard unavailable")

    class FakeKeyboard:
        def __init__(self) -> None:
            self.pressed: list[str] = []
            self.inserted: list[str] = []

        def press(self, key: str) -> None:
            self.pressed.append(key)

        def insert_text(self, text: str) -> None:
            self.inserted.append(text)

    class FakePage:
        def __init__(self) -> None:
            self.context = FakeContext()
            self.keyboard = FakeKeyboard()

    class FakeEditor:
        def get_attribute(self, name: str) -> str | None:
            return "true"

        def click(self, timeout: int) -> None:
            return None

        def evaluate(self, script: str, text: str):
            raise RuntimeError("dom commit unsupported")

        def inner_text(self) -> str:
            return ""

    page = FakePage()
    bridge._enter_message_text(
        page=page,
        editor=FakeEditor(),
        message_text=message,
    )

    assert page.keyboard.inserted == [message]
    assert page.keyboard.pressed == [
        "Control+A",
        "Backspace",
        "Control+A",
        "Backspace",
        "Control+A",
        "Backspace",
    ]


def test_large_contenteditable_dom_commit_returns_stage_diagnostics(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    message = "line one\n\nline three\n" * 300

    class FakeContext:
        def grant_permissions(self, permissions, origin):
            raise RuntimeError("clipboard unavailable")

    class FakeKeyboard:
        def __init__(self) -> None:
            self.pressed: list[str] = []
            self.inserted: list[str] = []

        def press(self, key: str) -> None:
            self.pressed.append(key)

        def insert_text(self, text: str) -> None:
            self.inserted.append(text)

    class FakePage:
        def __init__(self) -> None:
            self.context = FakeContext()
            self.keyboard = FakeKeyboard()

    class FakeEditor:
        def __init__(self) -> None:
            self.text = ""
            self.script = ""

        def get_attribute(self, name: str) -> str | None:
            return "true"

        def click(self, timeout: int) -> None:
            return None

        def evaluate(self, script: str, text: str):
            self.script = script
            self.text = text
            return {
                "ok": True,
                "stage": "complete",
                "errorName": "",
                "errorMessage": "",
                "insertedLength": len(text),
            }

        def inner_text(self) -> str:
            return self.text

    page = FakePage()
    editor = FakeEditor()
    bridge._enter_message_text(
        page=page,
        editor=editor,
        message_text=message,
    )

    assert "replaceChildren" in editor.script
    assert "result.stage = 'replace_children'" in editor.script
    assert "result.errorMessage" in editor.script
    assert page.keyboard.inserted == []


def test_completed_response_extends_wait_while_generation_is_active(
    tmp_path: Path,
) -> None:
    base = _config(tmp_path)
    bridge = ChatGPTBrowserBridge(
        BrowserBridgeConfig(
            chrome_executable=base.chrome_executable,
            profile_directory=base.profile_directory,
            xvfb_run_executable=base.xvfb_run_executable,
            response_timeout_seconds=0.002,
            response_generation_grace_seconds=0.08,
            response_poll_interval_seconds=0.001,
            stable_response_seconds=0.001,
        )
    )

    class FakeMessage:
        def get_attribute(self, name: str) -> str:
            assert name == "data-message-id"
            return "assistant-new"

        def inner_text(self) -> str:
            return "Delayed but complete response"

    class FakeMessages:
        def __init__(self) -> None:
            self.calls = 0

        def count(self) -> int:
            self.calls += 1
            return 0 if self.calls < 8 else 1

        def nth(self, index: int):
            assert index == 0
            return FakeMessage()

    messages = FakeMessages()

    class FakePage:
        def locator(self, selector: str):
            assert selector == '[data-message-author-role="assistant"]'
            return messages

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    bridge._generation_is_active = lambda page: messages.calls < 8

    result = bridge._wait_for_completed_response(
        page=FakePage(),
        baseline_count=0,
        baseline_signatures=(),
    )

    assert result == ("Delayed but complete response", "assistant-new")


def test_polish_download_button_is_generated_file_candidate(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def get_attribute(self, name):
            if name == "class":
                return "behavior-btn"
            return None

        def inner_text(self):
            return "Pobierz PSKI Foundation Sources 01"

    assert bridge._is_generated_file_candidate(FakeCandidate(), "", None)


def test_trigger_candidate_download_uses_open_preview_after_file_card_click(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeDownloadInfo:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            raise PlaywrightTimeoutError("no native download")

    class FakePage:
        def __init__(self):
            self.handler = None

        def on(self, name, handler):
            assert name == "response"
            self.handler = handler

        def remove_listener(self, name, handler):
            assert name == "response"
            assert handler is self.handler

        def expect_download(self, timeout):
            return FakeDownloadInfo()

        def wait_for_timeout(self, milliseconds):
            assert milliseconds == 250

    class FakeCandidate:
        def scroll_into_view_if_needed(self):
            return None

        def click(self):
            return None

        def get_attribute(self, name):
            return None

        def inner_text(self):
            return "Pobierz PSKI Foundation Sources 01"

        def evaluate(self, script):
            if script == "(element) => element.tagName":
                return "BUTTON"
            raise AssertionError(script)

    expected_download = object()
    bridge._capture_download_from_open_preview = (
        lambda **kwargs: expected_download
    )

    result = bridge._trigger_candidate_download(
        page=FakePage(),
        candidate=FakeCandidate(),
        request=BrowserExchangeRequest(
            request_id="request",
            department_id="research",
            message_text="create file",
            create_new_thread=False,
            conversation_url="https://chatgpt.com/c/research",
        ),
        candidate_index=0,
    )

    assert result is expected_download


def test_large_contenteditable_clipboard_accepts_prosemirror_whitespace_variation(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    message = ("alpha\nbeta\n\ngamma\n" * 400).strip()

    class FakeContext:
        def grant_permissions(self, permissions, origin):
            return None

    class FakeEditor:
        def __init__(self) -> None:
            self.text = ""

        def get_attribute(self, name: str) -> str | None:
            return "true"

        def click(self, timeout: int) -> None:
            return None

        def inner_text(self) -> str:
            return self.text

    editor = FakeEditor()

    class FakeKeyboard:
        def __init__(self) -> None:
            self.pressed: list[str] = []
            self.inserted: list[str] = []

        def press(self, key: str) -> None:
            self.pressed.append(key)
            if key == "Control+V":
                editor.text = message.replace("\n", "\n\n").replace(" ", "\u00a0")

        def insert_text(self, text: str) -> None:
            self.inserted.append(text)

    class FakePage:
        def __init__(self) -> None:
            self.context = FakeContext()
            self.keyboard = FakeKeyboard()

        def evaluate(self, script: str, text: str) -> bool:
            return True

    page = FakePage()
    bridge._enter_message_text(
        page=page,
        editor=editor,
        message_text=message,
    )

    assert page.keyboard.inserted == []
    assert page.keyboard.pressed == ["Control+A", "Backspace", "Control+V"]


def test_behavior_button_without_download_word_is_generated_artifact_candidate(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeCandidate:
        def get_attribute(self, name):
            if name == "class":
                return "behavior-btn entity-underline"
            return None

        def inner_text(self):
            return "PSKI Scientific Publications 01"

    assert bridge._is_generated_file_candidate(FakeCandidate(), "", None)


def test_request_preserves_attachment_paths(tmp_path: Path) -> None:
    attachment = tmp_path / "validation.log"
    attachment.write_text("198 passed", encoding="utf-8")

    request = BrowserExchangeRequest(
        request_id="request-with-file",
        department_id="core",
        message_text="Review attached validation.",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
        attachment_paths=(attachment,),
    )

    assert request.attachment_paths == (attachment,)


def test_upload_attachments_uses_real_file_input_and_confirms_names(
    tmp_path: Path,
) -> None:
    attachment = tmp_path / "validation.log"
    attachment.write_text("198 passed", encoding="utf-8")
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    bridge._active_request = BrowserExchangeRequest(
        request_id="request-upload",
        department_id="core",
        message_text="Review attached validation.",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
        attachment_paths=(attachment,),
    )

    selected_files = []

    class FakeFileInput:
        def set_input_files(self, paths, timeout):
            selected_files.append(paths)

    class FakeFileInputs:
        def count(self):
            return 1

        def set_input_files(self, paths, timeout):
            return FakeFileInput().set_input_files(paths, timeout)

        @property
        def first(self):
            return FakeFileInput()

    class FakeBody:
        def inner_text(self, timeout):
            return "validation.log.txt"

    class FakeAttachmentTile:
        @property
        def last(self):
            return self

        def count(self):
            return 1

        def evaluate(self, script):
            assert "waitingButton" in script
            return {
                "waiting": False,
                "waitingButton": False,
                "spinning": False,
                "progress": False,
                "removeButton": True,
            }

    class FakePage:
        def locator(self, selector):
            if selector == 'input#upload-files':
                return FakeFileInputs()
            if selector == "body":
                return FakeBody()
            if selector == '[role="group"][aria-label="validation.log.txt"]':
                return FakeAttachmentTile()
            raise AssertionError(selector)

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None

    bridge._upload_attachments(
        page=FakePage(),
        attachment_paths=(attachment,),
    )

    assert len(selected_files) == 1
    uploaded = Path(selected_files[0])
    assert uploaded.name == "validation.log.txt"
    assert uploaded.read_text(encoding="utf-8") == "198 passed"


def test_upload_attachments_rejects_missing_local_file(tmp_path: Path) -> None:
    from curvature_console.infrastructure.browser_bridge import (
        BrowserBridgeAttachmentUploadError,
    )

    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    with pytest.raises(
        BrowserBridgeAttachmentUploadError,
        match="Queued attachment is unavailable",
    ):
        bridge._upload_attachments(
            page=object(),
            attachment_paths=(tmp_path / "missing.log",),
        )



def test_large_message_with_attachment_uses_real_keyboard_input(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    message = "line one\nline two\n" * 400

    class FakeContext:
        def grant_permissions(self, permissions, origin):
            raise AssertionError("Clipboard must not be used with attachments")

    class FakeKeyboard:
        def __init__(self) -> None:
            self.pressed: list[str] = []
            self.inserted: list[str] = []

        def press(self, key: str) -> None:
            self.pressed.append(key)

        def insert_text(self, text: str) -> None:
            self.inserted.append(text)

    class FakePage:
        def __init__(self) -> None:
            self.context = FakeContext()
            self.keyboard = FakeKeyboard()

        def evaluate(self, script: str, text: str):
            raise AssertionError("Page clipboard evaluate must not be used")

    class FakeEditor:
        def get_attribute(self, name: str) -> str | None:
            return "true"

        def click(self, timeout: int) -> None:
            return None

        def evaluate(self, script: str, text: str):
            raise AssertionError("DOM commit must not be used with attachments")

    page = FakePage()
    editor = FakeEditor()
    bridge._enter_message_text(
        page=page,
        editor=editor,
        message_text=message,
        has_attachments=True,
    )

    assert page.keyboard.inserted == [message]
    assert page.keyboard.pressed == ["Control+A", "Backspace"]


def test_submit_message_does_not_press_enter_when_visible_send_stays_disabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = BrowserBridgeConfig(
        chrome_executable=_config(tmp_path).chrome_executable,
        profile_directory=tmp_path / "profile",
        editor_timeout_seconds=0.01,
    )
    bridge = ChatGPTBrowserBridge(config)

    class FakeButton:
        def is_visible(self):
            return True

        def is_enabled(self):
            return False

    class FakeLocator:
        def __init__(self, button=None) -> None:
            self.button = button

        def count(self):
            return 1 if self.button is not None else 0

        def nth(self, index):
            assert index == 0
            return self.button

    class FakeKeyboard:
        def press(self, key):
            raise AssertionError("Enter must not be used for a disabled Send button")

    class FakePage:
        def __init__(self) -> None:
            self.keyboard = FakeKeyboard()
            self.button = FakeButton()

        def locator(self, selector):
            if selector == 'button[data-testid="send-button"]':
                return FakeLocator(self.button)
            return FakeLocator()

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.time.sleep",
        lambda seconds: None,
    )

    with pytest.raises(BrowserBridgeMessageNotReady, match="Send button disabled"):
        bridge._submit_message(
            page=FakePage(),
            editor=object(),
            baseline_user_count=2,
        )


def test_large_message_with_attachment_keyboard_path_preserves_full_payload(
    tmp_path: Path,
) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    message = "alpha\nbeta\n" * 500

    class FakeKeyboard:
        def __init__(self, editor) -> None:
            self.editor = editor
            self.pressed: list[str] = []
            self.inserted: list[str] = []

        def press(self, key: str) -> None:
            self.pressed.append(key)
            if key == "Backspace":
                self.editor.text = ""

        def insert_text(self, text: str) -> None:
            self.inserted.append(text)
            self.editor.text += text

    class FakeEditor:
        def __init__(self) -> None:
            self.text = ""

        def get_attribute(self, name: str) -> str | None:
            return "true"

        def click(self, timeout: int) -> None:
            return None

        def inner_text(self) -> str:
            return self.text

    class FakePage:
        def __init__(self, editor) -> None:
            self.keyboard = FakeKeyboard(editor)

    editor = FakeEditor()
    page = FakePage(editor)
    bridge._enter_message_text(
        page=page,
        editor=editor,
        message_text=message,
        has_attachments=True,
    )

    assert editor.text == message
    assert page.keyboard.inserted == [message]
    assert page.keyboard.pressed == ["Control+A", "Backspace"]


def test_bridge_cancel_sets_cooperative_flag(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    assert bridge.cancellation_requested is False
    bridge.cancel()
    assert bridge.cancellation_requested is True


def test_log_attachment_normalization_contract_is_present() -> None:
    source = Path(
        "src/curvature_console/infrastructure/browser_bridge.py"
    ).read_text(encoding="utf-8")
    assert 'source.suffix.casefold() == ".log"' in source
    assert 'source.name + ".txt"' in source
    assert "cursor-wait" in source


def test_cancelled_exception_is_public_bridge_error() -> None:
    assert issubclass(BrowserBridgeCancelled, BrowserBridgeError)

def test_upload_attachments_prefers_general_upload_input(tmp_path: Path) -> None:
    attachment = tmp_path / "snapshot.zip"
    attachment.write_bytes(b"PK-test")
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    bridge._active_request = BrowserExchangeRequest(
        request_id="request-general-input",
        department_id="core",
        message_text="Review attachment.",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
        attachment_paths=(attachment,),
    )
    selected: list[str] = []

    class Input:
        def count(self):
            return 1

        def set_input_files(self, paths, timeout):
            selected.append(paths)

    class Body:
        def inner_text(self, timeout):
            return "snapshot.zip"

    class Tile:
        @property
        def last(self):
            return self

        def count(self):
            return 1

        def evaluate(self, script):
            return {
                "waiting": False,
                "waitingButton": False,
                "spinning": False,
                "progress": False,
                "removeButton": True,
            }

    class Page:
        def locator(self, selector):
            if selector == 'input#upload-files':
                return Input()
            if selector == "body":
                return Body()
            if selector == '[role="group"][aria-label="snapshot.zip"]':
                return Tile()
            raise AssertionError(selector)

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    bridge._upload_attachments(page=Page(), attachment_paths=(attachment,))
    assert selected == [str(attachment.resolve())]


def test_attachment_readiness_ignores_hidden_progress_dom(tmp_path: Path) -> None:
    attachment = tmp_path / "snapshot.zip"
    attachment.write_bytes(b"PK-test")
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    bridge._active_request = BrowserExchangeRequest(
        request_id="request-hidden-progress",
        department_id="core",
        message_text="Review attachment.",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
        attachment_paths=(attachment,),
    )

    class Input:
        def count(self):
            return 1

        def set_input_files(self, paths, timeout):
            return None

    class Body:
        def inner_text(self, timeout):
            return "snapshot.zip"

    class Tile:
        @property
        def last(self):
            return self

        def count(self):
            return 1

        def evaluate(self, script):
            assert "getComputedStyle" in script
            return {
                "waiting": False,
                "waitingButton": False,
                "spinning": False,
                "progress": False,
                "removeButton": True,
            }

    class Page:
        def locator(self, selector):
            if selector == 'input#upload-files':
                return Input()
            if selector == "body":
                return Body()
            if selector == '[role="group"][aria-label="snapshot.zip"]':
                return Tile()
            raise AssertionError(selector)

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    bridge._upload_attachments(page=Page(), attachment_paths=(attachment,))


def test_multi_attachment_upload_is_sequential_and_waits_for_each_file(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "snapshot.zip"
    snapshot.write_bytes(b"PK-test")
    validation = tmp_path / "validation.txt"
    validation.write_text("211 passed", encoding="utf-8")
    bridge = ChatGPTBrowserBridge(_config(tmp_path))
    bridge._active_request = BrowserExchangeRequest(
        request_id="request-sequential-multi-upload",
        department_id="core",
        message_text="Review attachments.",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
        attachment_paths=(snapshot, validation),
    )

    selections: list[str] = []
    polls = {"snapshot.zip": 0, "validation.txt": 0}

    class Input:
        def count(self):
            return 1

        def set_input_files(self, path, timeout):
            selections.append(path)

    class Body:
        def inner_text(self, timeout):
            return "snapshot.zip validation.txt"

    class Tile:
        def __init__(self, name: str) -> None:
            self.name = name

        @property
        def last(self):
            return self

        def count(self):
            return 1

        def evaluate(self, script):
            polls[self.name] += 1
            waiting = polls[self.name] == 1
            return {
                "waiting": waiting,
                "waitingButton": waiting,
                "spinning": False,
                "progress": False,
                "removeButton": True,
            }

    class Page:
        def locator(self, selector):
            if selector == 'input#upload-files':
                return Input()
            if selector == "body":
                return Body()
            if selector == '[role="group"][aria-label="snapshot.zip"]':
                return Tile("snapshot.zip")
            if selector == '[role="group"][aria-label="validation.txt"]':
                return Tile("validation.txt")
            raise AssertionError(selector)

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    bridge._upload_attachments(
        page=Page(),
        attachment_paths=(snapshot, validation),
    )

    assert selections == [str(snapshot.resolve()), str(validation.resolve())]
    assert polls["snapshot.zip"] >= 2
    assert polls["validation.txt"] >= 2


def test_attachment_readiness_accepts_stable_unknown_after_waiting(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attachment = tmp_path / "runtime.log"
    attachment.write_text("runtime", encoding="utf-8")
    config = BrowserBridgeConfig(
        chrome_executable=_config(tmp_path).chrome_executable,
        profile_directory=tmp_path / "profile",
        attachment_upload_timeout_seconds=10.0,
    )
    bridge = ChatGPTBrowserBridge(config)
    bridge._active_request = BrowserExchangeRequest(
        request_id="request-stable-unknown",
        department_id="console-development",
        message_text="Review attachment.",
        create_new_thread=False,
        conversation_url=BOOTSTRAP_CONVERSATION_URLS["core"],
        attachment_paths=(attachment,),
    )

    clock = {"value": 0.0}
    polls = {"count": 0}

    def monotonic() -> float:
        return clock["value"]

    def sleep(seconds: float) -> None:
        clock["value"] += seconds

    class Input:
        def count(self):
            return 1

        def set_input_files(self, paths, timeout):
            return None

    class Body:
        def inner_text(self, timeout):
            return "runtime.log.txt"

    class Tile:
        @property
        def last(self):
            return self

        def count(self):
            return 1

        def evaluate(self, script):
            polls["count"] += 1
            waiting = polls["count"] == 1
            return {
                "waiting": waiting,
                "waitingButton": waiting,
                "spinning": False,
                "progress": False,
                "removeButton": False,
            }

    class Page:
        def locator(self, selector):
            if selector == 'input#upload-files':
                return Input()
            if selector == "body":
                return Body()
            if selector == '[role="group"][aria-label="runtime.log.txt"]':
                return Tile()
            raise AssertionError(selector)

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.time.monotonic",
        monotonic,
    )
    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.time.sleep",
        sleep,
    )

    bridge._upload_attachments(page=Page(), attachment_paths=(attachment,))

    assert polls["count"] >= 5


def test_attachment_readiness_does_not_accept_brief_unknown_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attachment = tmp_path / "validation.txt"
    attachment.write_text("224 passed", encoding="utf-8")
    config = BrowserBridgeConfig(
        chrome_executable=_config(tmp_path).chrome_executable,
        profile_directory=tmp_path / "profile",
        attachment_upload_timeout_seconds=10.0,
    )
    bridge = ChatGPTBrowserBridge(config)

    clock = {"value": 0.0}
    states = iter(["waiting", "unknown", "unknown", "ready"])

    def monotonic() -> float:
        return clock["value"]

    def sleep(seconds: float) -> None:
        clock["value"] += seconds

    class Input:
        def count(self):
            return 1

        def set_input_files(self, paths, timeout):
            return None

    class Body:
        def inner_text(self, timeout):
            return "validation.txt"

    class Tile:
        @property
        def last(self):
            return self

        def count(self):
            return 1

        def evaluate(self, script):
            state = next(states)
            return {
                "waiting": state == "waiting",
                "waitingButton": state == "waiting",
                "spinning": False,
                "progress": False,
                "removeButton": state == "ready",
            }

    class Page:
        def locator(self, selector):
            if selector == 'input#upload-files':
                return Input()
            if selector == "body":
                return Body()
            if selector == '[role="group"][aria-label="validation.txt"]':
                return Tile()
            raise AssertionError(selector)

    bridge._assert_runtime_alive = lambda page: None
    bridge._raise_for_human_verification = lambda page: None
    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.time.monotonic",
        monotonic,
    )
    monkeypatch.setattr(
        "curvature_console.infrastructure.browser_bridge.time.sleep",
        sleep,
    )

    bridge._upload_attachments(page=Page(), attachment_paths=(attachment,))

    assert clock["value"] == pytest.approx(0.75)


def test_completed_assistant_message_prefers_confirmed_message_id(tmp_path: Path) -> None:
    bridge = ChatGPTBrowserBridge(_config(tmp_path))

    class FakeLocator:
        def __init__(self, items):
            self.items = items
        def count(self):
            return len(self.items)
        def nth(self, index):
            return self.items[index]
        @property
        def last(self):
            return self.items[-1]

    class FakeMessage:
        def __init__(self, message_id, text):
            self.message_id = message_id
            self.text = text
        def inner_text(self):
            return self.text

    old = FakeMessage("old-id", "Old response with stale file")
    new = FakeMessage("new-id", "New response with current file")

    class FakePage:
        def locator(self, selector):
            if 'data-message-id="new-id"' in selector:
                return FakeLocator([new])
            return FakeLocator([])

    resolved = bridge._completed_assistant_message(
        page=FakePage(),
        assistant_messages=FakeLocator([new, old]),
        response_message_id="new-id",
        response_text="New response with current file",
    )

    assert resolved is new
