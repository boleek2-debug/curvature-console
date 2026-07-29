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
    BrowserBridgeConfig,
    BrowserBridgeEditorUnavailable,
    BrowserBridgeMessageNotConfirmed,
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
