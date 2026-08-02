"""Deterministic browser automation for the shared Curvature ChatGPT Project."""

from __future__ import annotations

import json
import logging
import os
import re
import signal
import socket
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.sync_api import sync_playwright

from curvature_console.infrastructure.runtime_logging import (
    get_runtime_logger,
)


SHARED_PROJECT_NAME: Final[str] = "Curvature"
SHARED_PROJECT_URL: Final[str] = (
    "https://chatgpt.com/g/"
    "g-p-6a5ccf24ed988191b1589e5beca5b7c5/project"
)

# These URLs are used only to initialise an empty local SQLite route table.
# After bootstrap, SQLite is the routing source of truth.
BOOTSTRAP_CONVERSATION_URLS: Final[dict[str, str]] = {
    "project": (
        "https://chatgpt.com/c/"
        "6a58d168-2cf8-83eb-a4fe-76e818cef2d2"
    ),
    "core": (
        "https://chatgpt.com/c/"
        "6a553afb-7878-83ed-b352-99738a964dfe"
    ),
    "research": (
        "https://chatgpt.com/c/"
        "6a5b7350-50b4-83eb-9d07-cbd0e0c8d4a3"
    ),
}

ASSISTANT_MESSAGE_SELECTOR: Final[str] = (
    '[data-message-author-role="assistant"]'
)
USER_MESSAGE_SELECTOR: Final[str] = '[data-message-author-role="user"]'
MESSAGE_EDITOR_SELECTORS: Final[tuple[str, ...]] = (
    "#prompt-textarea",
    'div.ProseMirror[contenteditable="true"]',
    '[contenteditable="true"][data-virtualkeyboard="true"]',
    'textarea[placeholder*="Message"]',
)
SEND_BUTTON_SELECTORS: Final[tuple[str, ...]] = (
    'button[data-testid="send-button"]',
    'button[aria-label="Send prompt"]',
    'button[aria-label="Send message"]',
    'button[aria-label="Wyślij monit"]',
    'button[aria-label="Wyślij wiadomość"]',
)
CONVERSATION_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"/c/([0-9A-Za-z-]+)(?:/|$)"
)


class BrowserBridgeStage(StrEnum):
    """Visible lifecycle stages for one browser-mediated exchange."""

    CONNECTING = "Connecting"
    LAUNCHING_BROWSER = "Launching browser"
    OPENING_DEDICATED_PAGE = "Opening dedicated page"
    NAVIGATING = "Navigating"
    VERIFYING_ROUTE = "Verifying route"
    LOCATING_EDITOR = "Locating editor"
    UPLOADING_ATTACHMENTS = "Uploading attachments"
    ENTERING_MESSAGE = "Entering message"
    SENDING = "Sending"
    VERIFYING_USER_MESSAGE = "Verifying user message"
    WAITING_FOR_RESPONSE = "Waiting for response"
    RECEIVING = "Receiving"
    CAPTURING_DOWNLOADS = "Capturing downloads"
    HUMAN_ACTION_REQUIRED = "Human action required"
    COMPLETED = "Completed"
    CLEANING_UP = "Cleaning up"


class BrowserBridgeError(RuntimeError):
    """Base class for recoverable browser-bridge failures."""


class BrowserBridgeCancelled(BrowserBridgeError):
    """The operator cancelled the current browser exchange."""


class BrowserBridgeConnectionError(BrowserBridgeError):
    """Chrome or the local CDP endpoint is unavailable."""


class BrowserBridgeLoginRequired(BrowserBridgeError):
    """The dedicated Chrome profile is not logged in to ChatGPT."""


class BrowserBridgeAmbiguousTarget(BrowserBridgeError):
    """A required browser target is missing or ambiguous."""


class BrowserBridgeHumanVerificationRequired(BrowserBridgeError):
    """ChatGPT requires CAPTCHA or another human verification step."""


class BrowserBridgeTimeout(BrowserBridgeError):
    """ChatGPT did not complete the requested operation in time."""


class BrowserBridgeProcessExited(BrowserBridgeError):
    """The browser process, context or dedicated page disappeared."""


class BrowserBridgeEditorUnavailable(BrowserBridgeError):
    """The ChatGPT composer did not become available in the current mode."""


class BrowserBridgeAttachmentUploadError(BrowserBridgeError):
    """A queued local attachment was not uploaded to the ChatGPT composer."""


class BrowserBridgeRouteMismatch(BrowserBridgeError):
    """The dedicated page does not point to the requested conversation."""


class BrowserBridgeMessageNotReady(BrowserBridgeError):
    """The ChatGPT composer did not become ready for safe submission."""


class BrowserBridgeMessageNotConfirmed(BrowserBridgeError):
    """The user message did not appear in the requested conversation."""


class BrowserBridgeRouteUnverified(BrowserBridgeError):
    """A response was received, but the resulting URL was not verified."""

    def __init__(self, observed_url: str, response_text: str) -> None:
        self.observed_url = observed_url
        self.response_text = response_text
        super().__init__(
            "ChatGPT returned a response, but Curvature Console could not "
            "verify the conversation route. Observed page URL: "
            f"{observed_url}"
        )


@dataclass(frozen=True, slots=True)
class BrowserBridgeConfig:
    """Local Chrome, CDP and deterministic exchange settings."""

    chrome_executable: Path
    profile_directory: Path
    xvfb_run_executable: Path = Path("/usr/bin/xvfb-run")
    debugging_host: str = "127.0.0.1"
    debugging_port: int = 9222
    chatgpt_url: str = "https://chatgpt.com"
    browser_start_timeout_seconds: float = 15.0
    navigation_timeout_seconds: float = 45.0
    editor_timeout_seconds: float = 30.0
    message_confirmation_timeout_seconds: float = 30.0
    response_timeout_seconds: float = 180.0
    response_generation_grace_seconds: float = 600.0
    response_poll_interval_seconds: float = 0.5
    stable_response_seconds: float = 2.0
    human_action_timeout_seconds: float = 300.0
    process_shutdown_timeout_seconds: float = 5.0
    cdp_release_timeout_seconds: float = 5.0
    download_timeout_seconds: float = 15.0
    attachment_upload_timeout_seconds: float = 90.0
    download_inbox_directory: Path | None = None

    @property
    def cdp_url(self) -> str:
        return f"http://{self.debugging_host}:{self.debugging_port}"

    @classmethod
    def default(cls, project_root: Path | None = None) -> "BrowserBridgeConfig":
        root = (project_root or Path.cwd()).expanduser().resolve()
        return cls(
            chrome_executable=Path("/usr/bin/google-chrome-stable"),
            profile_directory=root / "data" / "browser-profile",
            download_inbox_directory=root / "data" / "inbox",
        )

    def validate(self) -> None:
        if not self.chrome_executable.is_file():
            raise FileNotFoundError(
                f"Chrome executable not found: {self.chrome_executable}"
            )
        if not 1 <= self.debugging_port <= 65535:
            raise ValueError("Debugging port must be between 1 and 65535.")

        positive_values = {
            "Browser start timeout": self.browser_start_timeout_seconds,
            "Navigation timeout": self.navigation_timeout_seconds,
            "Editor timeout": self.editor_timeout_seconds,
            "Message confirmation timeout":
                self.message_confirmation_timeout_seconds,
            "Response timeout": self.response_timeout_seconds,
            "Response generation grace":
                self.response_generation_grace_seconds,
            "Response poll interval": self.response_poll_interval_seconds,
            "Stable response duration": self.stable_response_seconds,
            "Human action timeout": self.human_action_timeout_seconds,
            "Process shutdown timeout":
                self.process_shutdown_timeout_seconds,
            "CDP release timeout": self.cdp_release_timeout_seconds,
            "Download timeout": self.download_timeout_seconds,
            "Attachment upload timeout":
                self.attachment_upload_timeout_seconds,
        }
        for label, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{label} must be positive.")




@dataclass(slots=True)
class _ResponseBackedDownload:
    """Download-compatible adapter backed by a captured fetch response."""

    suggested_filename: str
    body_bytes: bytes
    source_url: str

    def save_as(self, target: Path) -> None:
        target.write_bytes(self.body_bytes)


@dataclass(frozen=True, slots=True)
class CapturedDownload:
    """One generated file captured from a completed ChatGPT response."""

    original_filename: str
    saved_path: Path
    source_url: str
    size_bytes: int = 0


@dataclass(frozen=True, slots=True)
class BrowserExchangeRequest:
    """Immutable routing data for one browser-mediated exchange."""

    request_id: str
    department_id: str
    message_text: str
    create_new_thread: bool
    conversation_url: str | None = None
    confirmation_marker: str | None = None
    attachment_paths: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class BrowserExchangeResult:
    """One completed and request-bound browser exchange."""

    request_id: str
    department_id: str
    project_name: str
    project_url: str
    conversation_url: str
    response_text: str
    downloaded_files: tuple[CapturedDownload, ...] = ()


class ChromeLauncher:
    """Start Chrome visibly or on an invisible Xvfb display."""

    def __init__(self, config: BrowserBridgeConfig) -> None:
        self.config = config

    def command(self, *, headless: bool = False) -> tuple[str, ...]:
        """Return the Chrome command.

        ``headless=True`` means background operation for Console. It uses a
        normal headed Chrome inside Xvfb rather than Chromium headless mode,
        because ChatGPT/Cloudflare can serve a challenge page to headless
        Chromium.
        """

        self.config.validate()
        self.config.profile_directory.mkdir(parents=True, exist_ok=True)

        chrome_arguments = [
            str(self.config.chrome_executable),
            f"--remote-debugging-address={self.config.debugging_host}",
            f"--remote-debugging-port={self.config.debugging_port}",
            f"--user-data-dir={self.config.profile_directory}",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-size=1440,1000",
            self.config.chatgpt_url,
        ]

        if not headless:
            return tuple(chrome_arguments)

        if not self.config.xvfb_run_executable.is_file():
            raise FileNotFoundError(
                "Invisible browser mode requires xvfb-run. "
                f"Expected executable: {self.config.xvfb_run_executable}"
            )

        return (
            str(self.config.xvfb_run_executable),
            "--auto-servernum",
            "--server-args=-screen 0 1440x1000x24",
            *chrome_arguments,
        )

    def launch(self, *, headless: bool = False) -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            self.command(headless=headless),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


class ChatGPTBrowserBridge:
    """Run one deterministic request on one dedicated ChatGPT page."""

    def __init__(
        self,
        config: BrowserBridgeConfig,
        stage_callback: Callable[[BrowserBridgeStage], None] | None = None,
    ) -> None:
        self.config = config
        self._stage_callback = stage_callback
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._owned_process: subprocess.Popen[bytes] | None = None
        self._owned_process_group_id: int | None = None
        self._owned_process_is_headless = False
        self._dedicated_page: Page | None = None
        self._logger = get_runtime_logger("browser_bridge")
        self._active_request: BrowserExchangeRequest | None = None
        self._cancel_event = threading.Event()
        self._temporary_attachment_directory: tempfile.TemporaryDirectory[str] | None = None

    def _report_stage(self, stage: BrowserBridgeStage) -> None:
        request = self._active_request
        self._logger.info(
            "stage=%s request_id=%s department_id=%s headless=%s",
            stage.value,
            request.request_id if request is not None else "-",
            request.department_id if request is not None else "-",
            self._owned_process_is_headless,
        )
        if self._stage_callback is not None:
            self._stage_callback(stage)

    def connect(self) -> None:
        if self._browser is not None:
            return

        self._report_stage(BrowserBridgeStage.CONNECTING)
        self._logger.info("Connecting to CDP endpoint %s", self.config.cdp_url)
        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.connect_over_cdp(
                self.config.cdp_url
            )
        except Exception as exc:
            self._playwright.stop()
            self._playwright = None
            raise BrowserBridgeConnectionError(
                f"Cannot connect to Chrome at {self.config.cdp_url}."
            ) from exc

    def connect_or_launch_hybrid(self) -> None:
        try:
            self.connect()
            return
        except BrowserBridgeConnectionError:
            pass

        self._report_stage(BrowserBridgeStage.LAUNCHING_BROWSER)
        self._logger.info(
            "Launching normal Chrome on invisible Xvfb display profile=%s",
            self.config.profile_directory,
        )
        self._owned_process = ChromeLauncher(self.config).launch(headless=True)
        self._owned_process_group_id = self._owned_process.pid
        self._owned_process_is_headless = True
        try:
            self._wait_for_cdp()
        except Exception:
            self._terminate_owned_process()
            raise

    @property
    def cancellation_requested(self) -> bool:
        return self._cancel_event.is_set()

    def cancel(self) -> None:
        """Request cooperative cancellation and close the owned page."""

        self._cancel_event.set()
        request = self._active_request
        self._logger.info(
            "exchange_cancel_requested request_id=%s department_id=%s",
            request.request_id if request is not None else "-",
            request.department_id if request is not None else "-",
        )
        self._close_dedicated_page()
        self._terminate_owned_process()

    def close(self) -> None:
        """Close only the dedicated page and processes owned by this bridge."""

        self._report_stage(BrowserBridgeStage.CLEANING_UP)
        self._close_dedicated_page()
        try:
            self.disconnect()
        finally:
            self._terminate_owned_process()
            temporary_directory = self._temporary_attachment_directory
            self._temporary_attachment_directory = None
            if temporary_directory is not None:
                temporary_directory.cleanup()

    def disconnect(self) -> None:
        """Detach Playwright without closing externally owned Chrome."""

        playwright = self._playwright
        self._browser = None
        self._playwright = None
        if playwright is not None:
            try:
                playwright.stop()
            except Exception:
                pass

    def browser_context(self) -> BrowserContext:
        self._assert_browser_alive()
        assert self._browser is not None
        if not self._browser.contexts:
            raise BrowserBridgeConnectionError(
                "Connected Chrome has no browser context."
            )
        return self._browser.contexts[0]

    def open_dedicated_page(self) -> Page:
        """Create a page owned only by the current request."""

        self._assert_browser_alive()
        self._close_dedicated_page()
        self._report_stage(BrowserBridgeStage.OPENING_DEDICATED_PAGE)
        self._dedicated_page = self.browser_context().new_page()
        return self._dedicated_page

    def send_and_receive_hybrid(
        self,
        request: BrowserExchangeRequest,
    ) -> BrowserExchangeResult:
        self._validate_request(request)
        self.connect_or_launch_hybrid()

        self._active_request = request
        self._logger.info(
            "exchange_start request_id=%s department_id=%s "
            "create_new_thread=%s target_url=%s",
            request.request_id,
            request.department_id,
            request.create_new_thread,
            request.conversation_url or SHARED_PROJECT_URL,
        )
        try:
            try:
                result = self._send_and_receive_once(request)
            except (
                BrowserBridgeLoginRequired,
                BrowserBridgeHumanVerificationRequired,
            ) as exc:
                self._logger.warning(
                    "Visible recovery required request_id=%s reason=%s",
                    request.request_id,
                    type(exc).__name__,
                )
                if not self._owned_process_is_headless:
                    raise
                self._switch_to_visible_browser()
                self._wait_for_visible_user_recovery()
                result = self._send_and_receive_once(request)

            downloaded_files = getattr(
                result,
                "downloaded_files",
                (),
            )
            self._logger.info(
                "exchange_success request_id=%s department_id=%s "
                "conversation_url=%s downloads=%d",
                result.request_id,
                result.department_id,
                result.conversation_url,
                len(downloaded_files),
            )
            return result
        except Exception as exc:
            if self.cancellation_requested:
                if isinstance(exc, BrowserBridgeCancelled):
                    raise
                raise BrowserBridgeCancelled(
                    "Operation cancelled by the operator. "
                    "No further browser action was taken."
                ) from exc
            self._logger.exception(
                "exchange_failure request_id=%s department_id=%s",
                request.request_id,
                request.department_id,
            )
            raise
        finally:
            self._active_request = None

    def _validate_request(self, request: BrowserExchangeRequest) -> None:
        if not request.request_id.strip():
            raise ValueError("Request id must not be empty.")
        if not request.department_id.strip():
            raise ValueError("Department id must not be empty.")
        if not request.message_text.strip():
            raise ValueError("Message text must not be empty.")
        if not request.create_new_thread and not request.conversation_url:
            raise BrowserBridgeAmbiguousTarget(
                "No active conversation URL is stored for this department."
            )

    def _enter_message_text(
        self,
        *,
        page: Page,
        editor: Locator,
        message_text: str,
        has_attachments: bool = False,
    ) -> None:
        """Enter message text with bounded fast paths.

        Clipboard and direct-DOM fast paths are deliberately disabled when
        real attachments are present. ChatGPT may convert a large clipboard
        payload into ``Pasted markdown.md``, while direct DOM changes can leave
        its internal composer state unsynchronised and the Send button disabled.
        Attachment-bearing messages therefore use genuine keyboard insertion.

        Large ProseMirror payloads without attachments are first pasted
        through the browser clipboard so ChatGPT receives one normal paste
        transaction instead of thousands of per-character input operations.
        Direct DOM commit remains a bounded fallback, followed by keyboard
        insertion.
        """

        timeout_ms = int(self.config.editor_timeout_seconds * 1000)
        contenteditable = editor.get_attribute("contenteditable")

        if contenteditable == "true":
            editor.click(timeout=timeout_ms)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")

            if len(message_text) >= 4000:
                if has_attachments:
                    self._logger.info(
                        "message_entry_method "
                        "method=attachment_safe_keyboard_insert_text "
                        "contenteditable=true size=%d",
                        len(message_text),
                    )
                    page.keyboard.insert_text(message_text)
                    return

                expected_equivalent = self._normalize_editor_equivalence(
                    message_text
                )

                if not has_attachments:
                    self._logger.info(
                        "message_entry_method method=clipboard_paste "
                        "contenteditable=true size=%d",
                        len(message_text),
                    )
                    try:
                        page.context.grant_permissions(
                            ["clipboard-read", "clipboard-write"],
                            origin="https://chatgpt.com",
                        )
                        clipboard_written = page.evaluate(
                            """
                            async (text) => {
                                await navigator.clipboard.writeText(text);
                                return true;
                            }
                            """,
                            message_text,
                        )
                        editor.click(timeout=timeout_ms)
                        page.keyboard.press("Control+V")

                        deadline = time.monotonic() + 3.0
                        inserted_raw = ""
                        while time.monotonic() < deadline:
                            inserted_raw = self._read_editor_text(editor)
                            if (
                                self._normalize_editor_equivalence(inserted_raw)
                                == expected_equivalent
                            ):
                                self._logger.info(
                                    "message_entry_verified "
                                    "method=clipboard_paste size=%d "
                                    "observed_size=%d comparison=whitespace_normalized",
                                    len(message_text),
                                    len(self._normalize_message_text(inserted_raw)),
                                )
                                return
                            time.sleep(0.05)

                        self._logger.warning(
                            "message_entry_fast_path_mismatch "
                            "method=clipboard_paste clipboard_written=%s "
                            "expected_equivalent_size=%d "
                            "observed_equivalent_size=%d; trying_dom_commit",
                            bool(clipboard_written),
                            len(expected_equivalent),
                            len(self._normalize_editor_equivalence(inserted_raw)),
                        )
                    except Exception as exc:
                        self._logger.warning(
                            "message_entry_fast_path_failed "
                            "method=clipboard_paste error_type=%s error=%r; "
                            "trying_dom_commit",
                            type(exc).__name__,
                            str(exc),
                        )

                    editor.click(timeout=timeout_ms)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")

                self._logger.info(
                    "message_entry_method method=prosemirror_dom_commit "
                    "contenteditable=true size=%d",
                    len(message_text),
                )
                try:
                    result = editor.evaluate(
                        """
                        (element, text) => {
                            const result = {
                                ok: false,
                                stage: 'start',
                                errorName: '',
                                errorMessage: '',
                                insertedLength: 0,
                            };
                            try {
                                result.stage = 'focus';
                                element.focus();

                                result.stage = 'build_fragment';
                                const fragment = document.createDocumentFragment();
                                const LF = String.fromCharCode(10);
                                const CR = String.fromCharCode(13);
                                const lines = text.split(LF).map((line) =>
                                    line.endsWith(CR) ? line.slice(0, -1) : line
                                );
                                for (const line of lines) {
                                    const paragraph = document.createElement('p');
                                    if (line.length === 0) {
                                        paragraph.appendChild(document.createElement('br'));
                                    } else {
                                        paragraph.appendChild(document.createTextNode(line));
                                    }
                                    fragment.appendChild(paragraph);
                                }

                                result.stage = 'replace_children';
                                element.replaceChildren(fragment);
                                result.insertedLength = element.innerText.length;

                                result.stage = 'selection';
                                const selection = window.getSelection();
                                if (selection) {
                                    const range = document.createRange();
                                    range.selectNodeContents(element);
                                    range.collapse(false);
                                    selection.removeAllRanges();
                                    selection.addRange(range);
                                }

                                result.stage = 'dispatch_input';
                                element.dispatchEvent(new Event('input', {
                                    bubbles: true,
                                    composed: true,
                                }));

                                result.stage = 'complete';
                                result.ok = element.isConnected && element.innerText.length > 0;
                                result.insertedLength = element.innerText.length;
                                return result;
                            } catch (error) {
                                result.errorName = error && error.name ? error.name : 'Error';
                                result.errorMessage = error && error.message ? error.message : String(error);
                                try {
                                    result.insertedLength = element.innerText.length;
                                } catch (_) {
                                    result.insertedLength = -1;
                                }
                                return result;
                            }
                        }
                        """,
                        message_text,
                    )
                    inserted_raw = self._read_editor_text(editor)
                    inserted_equivalent = self._normalize_editor_equivalence(
                        inserted_raw
                    )
                    if (
                        isinstance(result, dict)
                        and result.get("ok")
                        and inserted_equivalent == expected_equivalent
                    ):
                        if has_attachments:
                            self._logger.info(
                                "message_entry_state_sync "
                                "method=keyboard_sentinel_roundtrip"
                            )
                            editor.click(timeout=timeout_ms)
                            page.keyboard.insert_text(" ")
                            page.keyboard.press("Backspace")
                            time.sleep(0.15)
                            inserted_raw = self._read_editor_text(editor)
                            inserted_equivalent = (
                                self._normalize_editor_equivalence(inserted_raw)
                            )
                            if inserted_equivalent != expected_equivalent:
                                self._logger.warning(
                                    "message_entry_state_sync_mismatch "
                                    "expected_equivalent_size=%d "
                                    "observed_equivalent_size=%d; "
                                    "falling_back_to_keyboard_insert_text",
                                    len(expected_equivalent),
                                    len(inserted_equivalent),
                                )
                            else:
                                self._logger.info(
                                    "message_entry_state_sync_verified "
                                    "method=keyboard_sentinel_roundtrip"
                                )
                                self._logger.info(
                                    "message_entry_verified "
                                    "method=prosemirror_dom_commit size=%d "
                                    "observed_size=%d "
                                    "comparison=whitespace_normalized",
                                    len(message_text),
                                    len(self._normalize_message_text(inserted_raw)),
                                )
                                return
                        else:
                            self._logger.info(
                                "message_entry_verified "
                                "method=prosemirror_dom_commit size=%d "
                                "observed_size=%d comparison=whitespace_normalized",
                                len(message_text),
                                len(self._normalize_message_text(inserted_raw)),
                            )
                            return
                    self._logger.warning(
                        "message_entry_dom_commit_result ok=%s stage=%s "
                        "error_name=%s error_message=%r inserted_length=%s "
                        "expected_equivalent_size=%d observed_equivalent_size=%d; "
                        "falling_back_to_keyboard_insert_text",
                        result.get("ok") if isinstance(result, dict) else None,
                        result.get("stage") if isinstance(result, dict) else None,
                        result.get("errorName") if isinstance(result, dict) else None,
                        result.get("errorMessage") if isinstance(result, dict) else repr(result),
                        result.get("insertedLength") if isinstance(result, dict) else None,
                        len(expected_equivalent),
                        len(inserted_equivalent),
                    )
                except Exception as exc:
                    self._logger.warning(
                        "message_entry_fast_path_failed "
                        "method=prosemirror_dom_commit error_type=%s error=%r; "
                        "falling_back_to_keyboard_insert_text",
                        type(exc).__name__,
                        str(exc),
                    )

                editor.click(timeout=timeout_ms)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")

            self._logger.info(
                "message_entry_method method=keyboard_insert_text "
                "contenteditable=true size=%d",
                len(message_text),
            )
            page.keyboard.insert_text(message_text)
            return

        self._logger.info(
            "message_entry_method method=locator_fill "
            "contenteditable=%s size=%d",
            contenteditable,
            len(message_text),
        )
        editor.fill(message_text, timeout=timeout_ms)

    def _submit_message(
        self,
        *,
        page: Page,
        editor: Locator,
        baseline_user_count: int,
    ) -> str:
        """Submit and verify that the composer reacted to activation.

        ChatGPT can expose an enabled Send button whose click returns without
        actually submitting the current composer. After clicking, the bridge
        therefore waits for one of two concrete effects: the composer becomes
        empty or a new user turn appears. If neither happens, Enter is used as
        a bounded fallback. Final request-marker confirmation remains
        authoritative.
        """

        timeout_seconds = self.config.editor_timeout_seconds
        deadline = time.monotonic() + timeout_seconds
        last_diagnostics: list[str] = []
        saw_visible_send_button = False

        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)
            diagnostics: list[str] = []

            for selector in SEND_BUTTON_SELECTORS:
                locator = page.locator(selector)
                count = locator.count()
                diagnostics.append(f"{selector}:count={count}")
                for index in range(count):
                    candidate = locator.nth(index)
                    try:
                        visible = candidate.is_visible()
                        enabled = candidate.is_enabled()
                        diagnostics.append(
                            f"{selector}[{index}]:visible={visible},"
                            f"enabled={enabled}"
                        )
                        if visible:
                            saw_visible_send_button = True
                        if visible and enabled:
                            candidate.click(
                                timeout=int(timeout_seconds * 1000)
                            )
                            self._logger.info(
                                "message_submit_method method=send_button "
                                "selector=%s index=%d",
                                selector,
                                index,
                            )
                            if self._wait_for_submission_effect(
                                page=page,
                                editor=editor,
                                baseline_user_count=baseline_user_count,
                            ):
                                return "send_button"

                            self._logger.warning(
                                "send_button_no_effect request_id=%s; "
                                "falling_back_to_enter",
                                self._active_request.request_id
                                if self._active_request is not None
                                else "-",
                            )
                            editor.click(
                                timeout=int(timeout_seconds * 1000)
                            )
                            page.keyboard.press("Enter")
                            self._logger.info(
                                "message_submit_method "
                                "method=send_button_then_keyboard_enter"
                            )
                            self._wait_for_submission_effect(
                                page=page,
                                editor=editor,
                                baseline_user_count=baseline_user_count,
                            )
                            return "send_button_then_keyboard_enter"
                    except Exception as exc:
                        diagnostics.append(
                            f"{selector}[{index}]:error="
                            f"{type(exc).__name__}"
                        )

            last_diagnostics = diagnostics
            time.sleep(0.25)

        request_id = (
            self._active_request.request_id
            if self._active_request is not None
            else "-"
        )
        if saw_visible_send_button:
            self._logger.error(
                "send_button_not_ready request_id=%s diagnostics=%s",
                request_id,
                " | ".join(last_diagnostics),
            )
            raise BrowserBridgeMessageNotReady(
                "ChatGPT kept the visible Send button disabled after the "
                "composer and attachments were populated. The message was "
                "not submitted, so no duplicate task was created."
            )

        self._logger.warning(
            "send_button_unavailable request_id=%s diagnostics=%s; "
            "falling_back_to_enter",
            request_id,
            " | ".join(last_diagnostics),
        )
        editor.click(timeout=int(timeout_seconds * 1000))
        page.keyboard.press("Enter")
        self._logger.info("message_submit_method method=keyboard_enter")
        self._wait_for_submission_effect(
            page=page,
            editor=editor,
            baseline_user_count=baseline_user_count,
        )
        return "keyboard_enter"

    def _wait_for_submission_effect(
        self,
        *,
        page: Page,
        editor: Locator,
        baseline_user_count: int,
        timeout_seconds: float = 3.0,
    ) -> bool:
        """Return true when submission visibly changed the conversation UI."""

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)

            current_user_count = page.locator(USER_MESSAGE_SELECTOR).count()
            if current_user_count > baseline_user_count:
                self._logger.info(
                    "message_submit_effect effect=new_user_message "
                    "baseline=%d current=%d",
                    baseline_user_count,
                    current_user_count,
                )
                return True

            editor_text = self._read_editor_text(editor)
            if not self._normalize_message_text(editor_text):
                self._logger.info(
                    "message_submit_effect effect=composer_cleared "
                    "baseline=%d current=%d",
                    baseline_user_count,
                    current_user_count,
                )
                return True

            time.sleep(self.config.response_poll_interval_seconds)

        self._logger.warning(
            "message_submit_effect_missing request_id=%s editor_excerpt=%r",
            self._active_request.request_id
            if self._active_request is not None
            else "-",
            self._normalize_message_text(self._read_editor_text(editor))[:160],
        )
        return False

    @staticmethod
    def _read_editor_text(editor: Locator) -> str:
        """Read either a contenteditable composer or an input/textarea."""

        try:
            if editor.get_attribute("contenteditable") == "true":
                return editor.inner_text()
            return editor.input_value()
        except Exception:
            return ""

    def _upload_attachments(
        self,
        *,
        page: Page,
        attachment_paths: tuple[Path, ...],
    ) -> None:
        """Upload files sequentially and wait for each file to become ready."""

        prepared_paths: list[Path] = []
        for raw_path in attachment_paths:
            source = Path(raw_path).expanduser().resolve()
            if not source.is_file():
                raise BrowserBridgeAttachmentUploadError(
                    f"Queued attachment is unavailable: {source}"
                )
            prepared = source
            if source.suffix.casefold() == ".log":
                if self._temporary_attachment_directory is None:
                    self._temporary_attachment_directory = tempfile.TemporaryDirectory(
                        prefix="curvature-console-attachments-"
                    )
                prepared = Path(self._temporary_attachment_directory.name) / (
                    source.name + ".txt"
                )
                prepared.write_bytes(source.read_bytes())
                self._logger.info(
                    "attachment_normalized original=%s upload_name=%s",
                    source.name,
                    prepared.name,
                )
            prepared_paths.append(prepared)

        if not prepared_paths:
            return

        request = self._active_request
        request_id = request.request_id if request is not None else "-"
        total = len(prepared_paths)
        ready_names: set[str] = set()

        def general_file_input() -> Locator:
            file_input = page.locator('input#upload-files')
            if file_input.count() >= 1:
                return file_input
            candidates = page.locator('input[type="file"]:not([accept*="image"])')
            if candidates.count() < 1:
                raise BrowserBridgeAttachmentUploadError(
                    "ChatGPT general file input is unavailable; "
                    "no attachment was sent."
                )
            return candidates.first

        def raise_for_page_upload_error() -> None:
            body_text = page.locator("body").inner_text(timeout=5000)
            lowered = body_text.casefold()
            for marker in (
                "failed to upload", "upload failed", "couldn't upload",
                "could not upload", "unsupported file", "file is too large",
                "nie udało się przesłać", "przesyłanie nie powiodło się",
            ):
                if marker in lowered:
                    raise BrowserBridgeAttachmentUploadError(
                        "ChatGPT reported an attachment upload failure: " + marker
                    )

        def tile_state(name: str) -> str:
            tile = page.locator(f'[role="group"][aria-label="{name}"]').last
            if tile.count() < 1:
                return "missing"
            details = tile.evaluate(
                """element => {
                    const visible = node => {
                        if (!node) return false;
                        const style = window.getComputedStyle(node);
                        const rect = node.getBoundingClientRect();
                        return style.display !== 'none'
                            && style.visibility !== 'hidden'
                            && Number(style.opacity || '1') > 0
                            && rect.width > 0
                            && rect.height > 0;
                    };
                    const waitingButton = Array.from(
                        element.querySelectorAll('.cursor-wait')
                    ).some(visible);
                    const spinning = Array.from(
                        element.querySelectorAll('.animate-spin')
                    ).some(visible);
                    const progress = Array.from(
                        element.querySelectorAll(
                            'svg circle[stroke-dashoffset], [role="progressbar"]'
                        )
                    ).some(visible);
                    const removeButton = Array.from(
                        element.querySelectorAll(
                            'button[aria-label^="Remove file"], '
                            + 'button[aria-label^="Usuń plik"]'
                        )
                    ).some(visible);
                    return {
                        waiting: waitingButton || spinning || progress,
                        waitingButton,
                        spinning,
                        progress,
                        removeButton,
                    };
                }"""
            )
            if details["waiting"]:
                return "waiting"
            if details["removeButton"]:
                return "ready"
            return "unknown"

        self._logger.info(
            "attachment_upload_started request_id=%s count=%d names=%s",
            request_id,
            total,
            ",".join(path.name for path in prepared_paths),
        )

        for index, prepared in enumerate(prepared_paths, start=1):
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)
            file_input = general_file_input()
            self._logger.info(
                "attachment_sequential_upload_started request_id=%s "
                "index=%d total=%d name=%s",
                request_id,
                index,
                total,
                prepared.name,
            )
            try:
                file_input.set_input_files(
                    str(prepared),
                    timeout=int(
                        self.config.attachment_upload_timeout_seconds * 1000
                    ),
                )
            except Exception as exc:
                raise BrowserBridgeAttachmentUploadError(
                    "ChatGPT rejected the queued attachment selection: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            upload_started_at = time.monotonic()
            deadline = (
                upload_started_at
                + self.config.attachment_upload_timeout_seconds
            )
            previous_state: str | None = None
            observed_waiting = False
            unknown_since: float | None = None
            unknown_polls = 0
            while time.monotonic() < deadline:
                self._assert_runtime_alive(page)
                self._raise_for_human_verification(page)
                raise_for_page_upload_error()
                state = tile_state(prepared.name)
                now = time.monotonic()
                if state != previous_state:
                    self._logger.info(
                        "attachment_state_transition request_id=%s "
                        "name=%s previous=%s current=%s",
                        request_id,
                        prepared.name,
                        previous_state or "none",
                        state,
                    )
                    previous_state = state

                if state == "waiting":
                    observed_waiting = True
                    unknown_since = None
                    unknown_polls = 0
                elif state == "unknown":
                    if unknown_since is None:
                        unknown_since = now
                        unknown_polls = 1
                    else:
                        unknown_polls += 1

                    # ChatGPT sometimes removes its visible progress marker before
                    # exposing a Remove button. The attachment tile is still
                    # present, no upload error is visible, and the file is already
                    # usable. Require a stable quiet tile before accepting this
                    # UI variant so a momentary DOM transition cannot be mistaken
                    # for readiness.
                    quiet_seconds = now - unknown_since
                    minimum_quiet_seconds = 1.5 if observed_waiting else 2.5
                    minimum_quiet_polls = 4 if observed_waiting else 6
                    if (
                        quiet_seconds >= minimum_quiet_seconds
                        and unknown_polls >= minimum_quiet_polls
                    ):
                        self._logger.warning(
                            "attachment_readiness_fallback request_id=%s "
                            "name=%s observed_waiting=%s quiet_seconds=%.2f "
                            "polls=%d",
                            request_id,
                            prepared.name,
                            observed_waiting,
                            quiet_seconds,
                            unknown_polls,
                        )
                        state = "ready"
                else:
                    unknown_since = None
                    unknown_polls = 0

                if state == "ready":
                    ready_names.add(prepared.name)
                    self._logger.info(
                        "attachment_sequential_upload_ready request_id=%s "
                        "index=%d total=%d name=%s",
                        request_id,
                        index,
                        total,
                        prepared.name,
                    )
                    break
                time.sleep(0.25)
            else:
                raise BrowserBridgeAttachmentUploadError(
                    "ChatGPT did not finish preparing the queued attachment "
                    "before timeout. "
                    f"State: {prepared.name}={previous_state or 'missing'}. "
                    "Nothing was sent."
                )

        self._logger.info(
            "attachment_upload_confirmed request_id=%s count=%d names=%s",
            request_id,
            total,
            ",".join(sorted(ready_names)),
        )


    def _send_and_receive_once(
        self,
        request: BrowserExchangeRequest,
    ) -> BrowserExchangeResult:
        page = self.open_dedicated_page()
        target_url = (
            SHARED_PROJECT_URL
            if request.create_new_thread
            else request.conversation_url
        )
        if target_url is None:
            raise BrowserBridgeAmbiguousTarget(
                "No active conversation URL is stored for this department."
            )

        self._report_stage(BrowserBridgeStage.NAVIGATING)
        self._logger.info(
            "Navigating dedicated page request_id=%s target_url=%s",
            request.request_id,
            target_url,
        )
        page.goto(
            target_url,
            wait_until="domcontentloaded",
            timeout=int(self.config.navigation_timeout_seconds * 1000),
        )
        self._assert_runtime_alive(page)
        self._raise_for_human_verification(page)

        if self._looks_logged_out(page):
            raise BrowserBridgeLoginRequired(
                "The dedicated Chrome profile is not logged in to ChatGPT."
            )

        if not request.create_new_thread:
            self._report_stage(BrowserBridgeStage.VERIFYING_ROUTE)
            self._verify_requested_route(target_url, page.url)

        self._report_stage(BrowserBridgeStage.LOCATING_EDITOR)
        editor = self._wait_for_message_editor(page)

        user_messages = page.locator(USER_MESSAGE_SELECTOR)
        assistant_messages = page.locator(ASSISTANT_MESSAGE_SELECTOR)
        baseline_user_count = user_messages.count()
        baseline_assistant_count = assistant_messages.count()
        baseline_assistant_signatures = (
            self._assistant_message_signatures(page)
        )
        self._logger.info(
            "message_baseline request_id=%s user_count=%d assistant_count=%d "
            "assistant_signatures=%d",
            request.request_id,
            baseline_user_count,
            baseline_assistant_count,
            len(baseline_assistant_signatures),
        )

        if request.attachment_paths:
            self._report_stage(BrowserBridgeStage.UPLOADING_ATTACHMENTS)
            self._upload_attachments(
                page=page,
                attachment_paths=request.attachment_paths,
            )

        self._report_stage(BrowserBridgeStage.ENTERING_MESSAGE)
        self._enter_message_text(
            page=page,
            editor=editor,
            message_text=request.message_text,
            has_attachments=bool(request.attachment_paths),
        )
        self._report_stage(BrowserBridgeStage.SENDING)
        self._submit_message(
            page=page,
            editor=editor,
            baseline_user_count=baseline_user_count,
        )

        self._report_stage(BrowserBridgeStage.VERIFYING_USER_MESSAGE)
        self._wait_for_confirmed_user_message(
            page=page,
            baseline_count=baseline_user_count,
            baseline_assistant_count=baseline_assistant_count,
            expected_text=request.message_text,
            confirmation_marker=request.confirmation_marker,
        )

        self._report_stage(BrowserBridgeStage.WAITING_FOR_RESPONSE)
        response_text = self._wait_for_completed_response(
            page=page,
            baseline_count=baseline_assistant_count,
            baseline_signatures=baseline_assistant_signatures,
        )
        self._report_stage(BrowserBridgeStage.RECEIVING)

        conversation_url = page.url
        if not self._is_conversation_url(conversation_url):
            raise BrowserBridgeRouteUnverified(
                observed_url=conversation_url,
                response_text=response_text,
            )

        if not request.create_new_thread:
            self._verify_requested_route(
                request.conversation_url or "",
                conversation_url,
            )

        self._report_stage(BrowserBridgeStage.CAPTURING_DOWNLOADS)
        latest_assistant_message = assistant_messages.nth(
            assistant_messages.count() - 1
        )
        downloaded_files = self._capture_generated_downloads(
            page=page,
            assistant_message=latest_assistant_message,
            request=request,
        )

        self._report_stage(BrowserBridgeStage.COMPLETED)
        return BrowserExchangeResult(
            request_id=request.request_id,
            department_id=request.department_id,
            project_name=SHARED_PROJECT_NAME,
            project_url=SHARED_PROJECT_URL,
            conversation_url=conversation_url,
            response_text=response_text,
            downloaded_files=downloaded_files,
        )


    def _capture_generated_downloads(
        self,
        page: Page,
        assistant_message: Locator,
        request: BrowserExchangeRequest,
    ) -> tuple[CapturedDownload, ...]:
        """Capture generated files from the completed assistant turn.

        ChatGPT may render a generated file outside the text node carrying
        ``data-message-author-role="assistant"``. The complete conversation
        turn is therefore searched, including links, buttons and file cards.
        """

        inbox_root = self.config.download_inbox_directory
        if inbox_root is None:
            self._logger.info(
                "download_capture_disabled request_id=%s reason=no_inbox",
                request.request_id,
            )
            return ()

        department_inbox = (
            inbox_root.expanduser().resolve() / request.department_id
        )
        department_inbox.mkdir(parents=True, exist_ok=True)

        scope = self._assistant_turn_scope(assistant_message)
        candidates = scope.locator(
            "a[href], button, [role='button'], "
            "[data-testid*='download' i], "
            "[data-testid*='file' i], "
            "[aria-label*='download' i], "
            "[aria-label*='file' i], "
            "[title*='download' i], "
            "[title*='file' i]"
        )

        captured: list[CapturedDownload] = []
        seen_signatures: set[str] = set()
        diagnostics: list[str] = []
        candidate_count = candidates.count()

        self._logger.info(
            "download_candidate_scan request_id=%s count=%d",
            request.request_id,
            candidate_count,
        )

        for index in range(candidate_count):
            candidate = candidates.nth(index)
            try:
                description = self._describe_download_candidate(candidate)
                diagnostics.append(f"{index}:{description}")

                href = candidate.get_attribute("href") or ""
                download_attribute = candidate.get_attribute("download")
                if not self._is_generated_file_candidate(
                    candidate,
                    href,
                    download_attribute,
                ):
                    continue
                if not candidate.is_visible():
                    continue

                signature = "|".join(
                    (
                        href,
                        download_attribute or "",
                        candidate.get_attribute("aria-label") or "",
                        candidate.inner_text().strip()[:160],
                    )
                )
                if signature in seen_signatures:
                    continue
                seen_signatures.add(signature)

                download = self._trigger_candidate_download(
                    page=page,
                    candidate=candidate,
                    request=request,
                    candidate_index=index,
                )
                if download is None:
                    continue
                original_filename = self._safe_download_filename(
                    download.suggested_filename
                    or download_attribute
                    or self._filename_from_candidate(candidate)
                    or "generated-file"
                )
                saved_path = self._collision_safe_path(
                    department_inbox,
                    original_filename,
                )
                download.save_as(saved_path)
                size_bytes = (
                    saved_path.stat().st_size
                    if saved_path.is_file()
                    else 0
                )
                record = CapturedDownload(
                    original_filename=original_filename,
                    saved_path=saved_path,
                    source_url=href,
                    size_bytes=size_bytes,
                )
                captured.append(record)
                self._logger.info(
                    "download_captured request_id=%s department_id=%s "
                    "original_filename=%r saved_path=%s size_bytes=%d",
                    request.request_id,
                    request.department_id,
                    original_filename,
                    saved_path,
                    size_bytes,
                )
            except PlaywrightTimeoutError:
                self._logger.warning(
                    "download_candidate_timeout request_id=%s index=%d "
                    "candidate=%s",
                    request.request_id,
                    index,
                    diagnostics[-1] if diagnostics else "[unavailable]",
                )
            except Exception:
                self._logger.exception(
                    "download_capture_failure request_id=%s index=%d "
                    "candidate=%s",
                    request.request_id,
                    index,
                    diagnostics[-1] if diagnostics else "[unavailable]",
                )

        if not captured:
            self._logger.warning(
                "download_capture_empty request_id=%s candidate_count=%d "
                "candidates=%s scope_html=%s",
                request.request_id,
                candidate_count,
                " || ".join(diagnostics[:40]) or "[none]",
                self._safe_locator_html(scope, 4000),
            )

        self._logger.info(
            "download_capture_complete request_id=%s count=%d",
            request.request_id,
            len(captured),
        )
        return tuple(captured)

    def _observe_file_activation_channels(
        self,
        page: Page,
        candidate: Locator,
        request: BrowserExchangeRequest,
        candidate_index: int,
    ) -> dict:
        """Observe all browser-visible channels used by a file-card activation."""

        events: dict[str, list] = {
            "requests": [],
            "responses": [],
            "downloads": [],
            "popups": [],
            "console": [],
        }

        def on_request(item):
            try:
                events["requests"].append(
                    {
                        "method": item.method,
                        "url": item.url,
                        "resource_type": item.resource_type,
                    }
                )
            except Exception:
                self._logger.exception(
                    "file_observer_request_capture_failed request_id=%s",
                    request.request_id,
                )

        def on_response(item):
            try:
                headers = item.headers
                events["responses"].append(
                    {
                        "status": item.status,
                        "url": item.url,
                        "content_type": headers.get("content-type", ""),
                        "content_disposition": headers.get(
                            "content-disposition", ""
                        ),
                    }
                )
            except Exception:
                self._logger.exception(
                    "file_observer_response_capture_failed request_id=%s",
                    request.request_id,
                )

        def on_download(item):
            try:
                events["downloads"].append(
                    {"suggested_filename": item.suggested_filename}
                )
            except Exception:
                self._logger.exception(
                    "file_observer_download_capture_failed request_id=%s",
                    request.request_id,
                )

        def on_popup(item):
            try:
                events["popups"].append({"url": item.url})
            except Exception:
                self._logger.exception(
                    "file_observer_popup_capture_failed request_id=%s",
                    request.request_id,
                )

        def on_console(item):
            try:
                events["console"].append(
                    {"type": item.type, "text": item.text}
                )
            except Exception:
                self._logger.exception(
                    "file_observer_console_capture_failed request_id=%s",
                    request.request_id,
                )

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("download", on_download)
        page.on("popup", on_popup)
        page.on("console", on_console)

        page.add_init_script(
            """
            (() => {
              if (window.__curvatureFileObserverInstalled) return;
              window.__curvatureFileObserverInstalled = true;
              window.__curvatureFileObserver = {
                fetches: [],
                xhrs: [],
                objectUrls: [],
                anchorClicks: [],
              };

              const originalFetch = window.fetch;
              window.fetch = async (...args) => {
                const input = args[0];
                const url = typeof input === "string"
                  ? input
                  : (input && input.url) || "";
                const method = (args[1] && args[1].method)
                  || (input && input.method)
                  || "GET";
                const startedAt = Date.now();
                try {
                  const response = await originalFetch(...args);
                  window.__curvatureFileObserver.fetches.push({
                    url,
                    method,
                    status: response.status,
                    contentType: response.headers.get("content-type") || "",
                    contentDisposition:
                      response.headers.get("content-disposition") || "",
                    startedAt,
                  });
                  return response;
                } catch (error) {
                  window.__curvatureFileObserver.fetches.push({
                    url,
                    method,
                    error: String(error),
                    startedAt,
                  });
                  throw error;
                }
              };

              const originalOpen = XMLHttpRequest.prototype.open;
              const originalSend = XMLHttpRequest.prototype.send;
              XMLHttpRequest.prototype.open = function(method, url, ...rest) {
                this.__curvatureMethod = method;
                this.__curvatureUrl = url;
                return originalOpen.call(this, method, url, ...rest);
              };
              XMLHttpRequest.prototype.send = function(...args) {
                this.addEventListener("loadend", () => {
                  window.__curvatureFileObserver.xhrs.push({
                    url: this.__curvatureUrl || "",
                    method: this.__curvatureMethod || "",
                    status: this.status,
                    contentType:
                      this.getResponseHeader("content-type") || "",
                    contentDisposition:
                      this.getResponseHeader("content-disposition") || "",
                  });
                }, { once: true });
                return originalSend.apply(this, args);
              };

              const originalCreateObjectURL = URL.createObjectURL;
              URL.createObjectURL = function(object) {
                const result = originalCreateObjectURL.call(URL, object);
                window.__curvatureFileObserver.objectUrls.push({
                  url: result,
                  type: object && object.type ? object.type : "",
                  size: object && typeof object.size === "number"
                    ? object.size
                    : null,
                });
                return result;
              };

              const originalAnchorClick = HTMLAnchorElement.prototype.click;
              HTMLAnchorElement.prototype.click = function() {
                window.__curvatureFileObserver.anchorClicks.push({
                  href: this.href || "",
                  download: this.download || "",
                  target: this.target || "",
                });
                return originalAnchorClick.call(this);
              };
            })();
            """
        )

        candidate.scroll_into_view_if_needed()
        candidate.click()
        page.wait_for_timeout(2000)

        browser_state = page.evaluate(
            """
            () => window.__curvatureFileObserver || {
              fetches: [],
              xhrs: [],
              objectUrls: [],
              anchorClicks: [],
            }
            """
        )

        result = {
            **events,
            "browser": browser_state,
        }
        self._logger.info(
            "file_activation_observation request_id=%s index=%d data=%s",
            request.request_id,
            candidate_index,
            json.dumps(result, ensure_ascii=False, sort_keys=True),
        )
        return result

    def _trigger_candidate_download(
        self,
        page: Page,
        candidate: Locator,
        request: BrowserExchangeRequest,
        candidate_index: int,
    ):
        """Capture either a native download or ChatGPT's fetch response."""

        direct_timeout_ms = min(
            int(self.config.download_timeout_seconds * 1000),
            5000,
        )
        candidate.scroll_into_view_if_needed()
        candidate_filename = (
            self._filename_from_candidate(candidate)
            or "generated-file"
        )

        activation_attempts = (
            ("locator_click", lambda: candidate.click()),
            (
                "coordinate_click",
                lambda: self._click_candidate_center(page, candidate),
            ),
            (
                "pointer_dispatch",
                lambda: self._dispatch_candidate_pointer_sequence(
                    candidate
                ),
            ),
            ("keyboard_enter", lambda: candidate.press("Enter")),
            ("keyboard_space", lambda: candidate.press("Space")),
        )

        for activation_name, activate in activation_attempts:
            attachment_responses = []

            def on_response(response) -> None:
                try:
                    disposition = response.headers.get(
                        "content-disposition", ""
                    ).lower()
                    is_estuary_content = (
                        "/backend-api/estuary/content" in response.url
                    )
                    if (
                        response.status == 200
                        and (
                            "attachment" in disposition
                            or is_estuary_content
                        )
                    ):
                        attachment_responses.append(response)
                except Exception:
                    self._logger.exception(
                        "download_response_probe_failure "
                        "request_id=%s index=%d method=%s",
                        request.request_id,
                        candidate_index,
                        activation_name,
                    )

            page.on("response", on_response)
            self._logger.info(
                "download_activation_attempt request_id=%s index=%d "
                "method=%s candidate=%s",
                request.request_id,
                candidate_index,
                activation_name,
                self._describe_download_candidate(candidate),
            )
            try:
                with page.expect_download(
                    timeout=direct_timeout_ms,
                ) as download_info:
                    activate()
                self._logger.info(
                    "download_activation_success request_id=%s index=%d "
                    "method=%s channel=native_download",
                    request.request_id,
                    candidate_index,
                    activation_name,
                )
                return download_info.value
            except PlaywrightTimeoutError:
                page.wait_for_timeout(250)
                if attachment_responses:
                    response = attachment_responses[-1]
                    body_bytes = response.body()
                    self._logger.info(
                        "download_activation_success request_id=%s index=%d "
                        "method=%s channel=fetch_response url=%s "
                        "size_bytes=%d",
                        request.request_id,
                        candidate_index,
                        activation_name,
                        response.url,
                        len(body_bytes),
                    )
                    return _ResponseBackedDownload(
                        suggested_filename=candidate_filename,
                        body_bytes=body_bytes,
                        source_url=response.url,
                    )

                self._logger.info(
                    "download_activation_no_event request_id=%s index=%d "
                    "method=%s",
                    request.request_id,
                    candidate_index,
                    activation_name,
                )
                if (
                    activation_name == "locator_click"
                    and candidate_filename == "generated-file"
                ):
                    preview_download = self._capture_download_from_open_preview(
                        page=page,
                        request=request,
                        candidate_index=candidate_index,
                    )
                    if preview_download is not None:
                        self._logger.info(
                            "download_activation_success request_id=%s "
                            "index=%d method=%s "
                            "channel=open_preview",
                            request.request_id,
                            candidate_index,
                            activation_name,
                        )
                        return preview_download
            except Exception:
                self._logger.exception(
                    "download_activation_failure request_id=%s index=%d "
                    "method=%s",
                    request.request_id,
                    candidate_index,
                    activation_name,
                )
            finally:
                page.remove_listener("response", on_response)

        self._logger.warning(
            "download_activation_exhausted request_id=%s index=%d "
            "candidate=%s",
            request.request_id,
            candidate_index,
            self._describe_download_candidate(candidate),
        )
        return None

    def _click_candidate_center(
        self,
        page: Page,
        candidate: Locator,
    ) -> None:
        """Click the visible centre point of the candidate."""

        box = candidate.bounding_box()
        if box is None:
            raise RuntimeError("Download candidate has no bounding box.")
        page.mouse.click(
            box["x"] + (box["width"] / 2),
            box["y"] + (box["height"] / 2),
        )

    def _dispatch_candidate_pointer_sequence(
        self,
        candidate: Locator,
    ) -> None:
        """Dispatch a complete pointer/mouse activation sequence."""

        candidate.evaluate(
            """
            (element) => {
              const events = [
                new PointerEvent("pointerdown", {
                  bubbles: true,
                  cancelable: true,
                  composed: true,
                  pointerId: 1,
                  pointerType: "mouse",
                  isPrimary: true,
                  button: 0,
                  buttons: 1,
                }),
                new MouseEvent("mousedown", {
                  bubbles: true,
                  cancelable: true,
                  composed: true,
                  button: 0,
                  buttons: 1,
                }),
                new PointerEvent("pointerup", {
                  bubbles: true,
                  cancelable: true,
                  composed: true,
                  pointerId: 1,
                  pointerType: "mouse",
                  isPrimary: true,
                  button: 0,
                  buttons: 0,
                }),
                new MouseEvent("mouseup", {
                  bubbles: true,
                  cancelable: true,
                  composed: true,
                  button: 0,
                  buttons: 0,
                }),
                new MouseEvent("click", {
                  bubbles: true,
                  cancelable: true,
                  composed: true,
                  button: 0,
                  buttons: 0,
                  detail: 1,
                }),
              ];
              for (const event of events) {
                element.dispatchEvent(event);
              }
            }
            """
        )

    def _capture_interaction_snapshot(self, page: Page) -> dict[str, object]:
        """Return bounded evidence focused on the active blocking layer."""

        script = """
        () => {
          const MAX_HTML = 12000;
          const MAX_CONTROLS = 80;

          const visible = (element) => {
            const style = window.getComputedStyle(element);
            const rect = element.getBoundingClientRect();
            return (
              style.display !== "none" &&
              style.visibility !== "hidden" &&
              Number(style.opacity || "1") !== 0 &&
              rect.width > 0 &&
              rect.height > 0
            );
          };

          const describe = (element, includeHtml = true) => {
            const rect = element.getBoundingClientRect();
            const style = window.getComputedStyle(element);
            const text = (element.innerText || element.textContent || "")
              .replace(/\\s+/g, " ")
              .trim()
              .slice(0, 600);
            const attributes = {};
            for (const name of [
              "role",
              "aria-label",
              "aria-modal",
              "aria-expanded",
              "aria-controls",
              "aria-haspopup",
              "data-state",
              "data-testid",
              "title",
              "href",
              "download",
              "class",
              "style",
            ]) {
              const value = element.getAttribute(name);
              if (value) {
                attributes[name] = value.slice(0, 1200);
              }
            }
            return {
              tag: element.tagName.toLowerCase(),
              attributes,
              text,
              rect: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
              },
              position: style.position,
              zIndex: style.zIndex,
              html: includeHtml
                ? element.outerHTML.replace(/\\s+/g, " ").slice(0, MAX_HTML)
                : "",
            };
          };

          const active = document.activeElement;

          const ancestors = [];
          let cursor = active;
          while (cursor && cursor !== document.body) {
            ancestors.push(describe(cursor, true));
            cursor = cursor.parentElement;
          }

          const closeButton = Array.from(
            document.querySelectorAll(
              [
                "button[data-testid='close-button']",
                "button[aria-label='Close']",
                "[role='button'][aria-label='Close']",
              ].join(",")
            )
          ).find(visible) || null;

          let layer = null;
          if (closeButton) {
            let node = closeButton;
            while (node && node !== document.body) {
              const role = node.getAttribute("role");
              const modal = node.getAttribute("aria-modal");
              const state = node.getAttribute("data-state");
              const style = window.getComputedStyle(node);
              const rect = node.getBoundingClientRect();
              const looksBlocking = (
                role === "dialog" ||
                modal === "true" ||
                state === "open" ||
                style.position === "fixed" ||
                style.position === "absolute"
              );
              const meaningfullyLarge = (
                rect.width >= 250 &&
                rect.height >= 150
              );
              if (looksBlocking && meaningfullyLarge) {
                layer = node;
                break;
              }
              node = node.parentElement;
            }

            if (!layer) {
              layer = closeButton.parentElement;
            }
          }

          const controls = [];
          if (layer) {
            for (const element of Array.from(
              layer.querySelectorAll(
                [
                  "a",
                  "button",
                  "[role='button']",
                  "[role='link']",
                  "[aria-label]",
                  "[data-testid]",
                ].join(",")
              )
            )) {
              if (!visible(element)) {
                continue;
              }
              controls.push(describe(element, true));
              if (controls.length >= MAX_CONTROLS) {
                break;
              }
            }
          }

          const body = document.body;
          return {
            url: location.href,
            title: document.title,
            body: {
              class: body.className || "",
              style: body.getAttribute("style") || "",
              dataScrollLocked: body.getAttribute("data-scroll-locked"),
            },
            activeElement: active ? describe(active, true) : null,
            activeAncestors: ancestors,
            closeButton: closeButton ? describe(closeButton, true) : null,
            layer: layer ? describe(layer, true) : null,
            layerControls: controls,
          };
        }
        """
        try:
            result = page.evaluate(script)
        except Exception:
            self._logger.exception("download_interaction_snapshot_failure")
            return {"error": "snapshot_failed"}
        return result if isinstance(result, dict) else {"value": result}

    def _diff_interaction_snapshots(
        self,
        before: dict[str, object],
        after: dict[str, object],
    ) -> dict[str, object]:
        """Summarise evidence relevant to the active blocking layer."""

        return {
            "bodyChanged": before.get("body") != after.get("body"),
            "activeElementChanged": (
                before.get("activeElement") != after.get("activeElement")
            ),
            "closeButtonAppeared": (
                before.get("closeButton") is None
                and after.get("closeButton") is not None
            ),
            "layerAppeared": (
                before.get("layer") is None
                and after.get("layer") is not None
            ),
            "afterLayer": after.get("layer"),
            "afterLayerControls": after.get("layerControls", []),
            "afterActiveAncestors": after.get("activeAncestors", []),
        }

    def _capture_download_from_open_preview(
        self,
        page: Page,
        request: BrowserExchangeRequest,
        candidate_index: int,
    ):
        """Find and activate the real Download control after a file-card click."""

        # File cards open an artifact preview asynchronously. Give the
        # preview a bounded moment to render, then inspect both semantic
        # Download controls and visible buttons whose text is Download/Pobierz.
        page.wait_for_timeout(1500)
        preview_snapshot = self._capture_interaction_snapshot(page)
        self._logger.info(
            "download_preview_state request_id=%s source_index=%d data=%s",
            request.request_id,
            candidate_index,
            json.dumps(preview_snapshot, ensure_ascii=False, sort_keys=True),
        )

        preview_candidates = page.locator(
            "a[download], "
            "a[href*='/backend-api/files/'], "
            "a[href*='files.oaiusercontent.com'], "
            "button[aria-label*='download' i], "
            "[role='button'][aria-label*='download' i], "
            "[data-testid*='download' i], "
            "[title*='download' i], "
            "button, [role='button']"
        )

        descriptions: list[str] = []
        visible_candidates: list[Locator] = []
        for index in range(preview_candidates.count()):
            preview_candidate = preview_candidates.nth(index)
            try:
                if not preview_candidate.is_visible():
                    continue
                description_text = (
                    preview_candidate.inner_text().strip().lower()
                )
                aria_label = (
                    preview_candidate.get_attribute("aria-label") or ""
                ).lower()
                title = (
                    preview_candidate.get_attribute("title") or ""
                ).lower()
                testid = (
                    preview_candidate.get_attribute("data-testid") or ""
                ).lower()
                href = preview_candidate.get_attribute("href") or ""
                download_attribute = preview_candidate.get_attribute(
                    "download"
                )
                is_download_control = bool(
                    download_attribute is not None
                    or "/backend-api/files/" in href
                    or "files.oaiusercontent.com" in href
                    or "download" in aria_label
                    or "download" in title
                    or "download" in testid
                    or description_text in {"download", "pobierz"}
                    or description_text.startswith("download ")
                    or description_text.startswith("pobierz ")
                )
                if not is_download_control:
                    continue
                visible_candidates.append(preview_candidate)
                descriptions.append(
                    f"{index}:"
                    f"{self._describe_download_candidate(preview_candidate)}"
                )
            except Exception:
                self._logger.exception(
                    "download_preview_candidate_inspection_failure "
                    "request_id=%s source_index=%d preview_index=%d",
                    request.request_id,
                    candidate_index,
                    index,
                )

        self._logger.info(
            "download_preview_scan request_id=%s source_index=%d "
            "visible_count=%d candidates=%s",
            request.request_id,
            candidate_index,
            len(visible_candidates),
            " || ".join(descriptions[:30]) or "[none]",
        )

        timeout_ms = int(self.config.download_timeout_seconds * 1000)
        for preview_index, preview_candidate in enumerate(
            visible_candidates
        ):
            try:
                with page.expect_download(
                    timeout=timeout_ms,
                ) as download_info:
                    preview_candidate.click()
                self._logger.info(
                    "download_preview_triggered request_id=%s "
                    "source_index=%d preview_index=%d",
                    request.request_id,
                    candidate_index,
                    preview_index,
                )
                return download_info.value
            except PlaywrightTimeoutError:
                self._logger.warning(
                    "download_preview_candidate_timeout request_id=%s "
                    "source_index=%d preview_index=%d",
                    request.request_id,
                    candidate_index,
                    preview_index,
                )
            except Exception:
                self._logger.exception(
                    "download_preview_candidate_failure request_id=%s "
                    "source_index=%d preview_index=%d",
                    request.request_id,
                    candidate_index,
                    preview_index,
                )

        self._logger.warning(
            "download_preview_unresolved request_id=%s source_index=%d "
            "page_html=%s",
            request.request_id,
            candidate_index,
            self._safe_locator_html(page.locator("body"), 5000),
        )
        return None

    def _assistant_turn_scope(self, assistant_message: Locator) -> Locator:
        """Return the complete assistant turn containing text and file cards."""

        article = assistant_message.locator("xpath=ancestor::article[1]")
        if article.count() > 0:
            return article.first

        conversation_turn = assistant_message.locator(
            "xpath=ancestor::*[contains(@data-testid, "
            "'conversation-turn')][1]"
        )
        if conversation_turn.count() > 0:
            return conversation_turn.first

        parent = assistant_message.locator("xpath=parent::*")
        if parent.count() > 0:
            return parent.first

        return assistant_message

    def _is_generated_file_candidate(
        self,
        candidate: Locator,
        href: str,
        download_attribute: str | None,
    ) -> bool:
        if self._is_generated_file_link(href, download_attribute):
            return True

        attributes = " ".join(
            filter(
                None,
                (
                    candidate.get_attribute("aria-label"),
                    candidate.get_attribute("title"),
                    candidate.get_attribute("data-testid"),
                ),
            )
        ).lower()
        text = candidate.inner_text().strip().lower()
        class_name = (candidate.get_attribute("class") or "").lower()

        # ChatGPT generated artifacts are currently rendered as a button with
        # the ``behavior-btn`` class and a human title, but no href, download
        # attribute, filename extension, or Download label. This is distinct
        # from ordinary response-action buttons and must be treated as a file
        # card so the bridge can open its preview and activate the real
        # download control.
        if "behavior-btn" in class_name and text:
            return True

        if (
            "download" in attributes
            or "download" in text
            or "pobierz" in attributes
            or text.startswith("pobierz ")
        ):
            return True

        if "coding citation" in attributes:
            return False

        file_hint = f"{attributes} {text}"
        return bool(
            re.search(
                r"\b[^/\s]+\."
                r"(txt|md|json|csv|pdf|png|jpe?g|webp|gif|docx?|xlsx?|"
                r"pptx?|zip|tar|gz|xml|yaml|yml|log)\b",
                file_hint,
                flags=re.IGNORECASE,
            )
        )

    def _filename_from_candidate(self, candidate: Locator) -> str | None:
        values = (
            candidate.get_attribute("download"),
            candidate.get_attribute("aria-label"),
            candidate.get_attribute("title"),
            candidate.inner_text().strip(),
        )
        for value in values:
            if not value:
                continue

            cleaned_value = re.sub(
                r"^\s*(?:download|open|save|file|pobierz)\s*[:\-–—]?\s*",
                "",
                value,
                flags=re.IGNORECASE,
            )

            match = re.search(
                r"([A-Za-z0-9._()-]+(?: [A-Za-z0-9._()-]+)*\."
                r"(?:txt|md|json|csv|pdf|png|jpe?g|webp|gif|docx?|xlsx?|"
                r"pptx?|zip|tar|gz|xml|yaml|yml|log))",
                cleaned_value,
                flags=re.IGNORECASE,
            )
            if match:
                return match.group(1).strip()
        return None

    def _describe_download_candidate(self, candidate: Locator) -> str:
        tag_name = candidate.evaluate("(element) => element.tagName")
        values = {
            "tag": str(tag_name).lower(),
            "href": candidate.get_attribute("href") or "",
            "download": candidate.get_attribute("download") or "",
            "aria": candidate.get_attribute("aria-label") or "",
            "title": candidate.get_attribute("title") or "",
            "testid": candidate.get_attribute("data-testid") or "",
            "text": candidate.inner_text().strip()[:240],
        }
        return ",".join(
            f"{key}={value!r}" for key, value in values.items()
        )

    def _safe_locator_html(
        self,
        locator: Locator,
        limit: int,
    ) -> str:
        try:
            html = locator.evaluate("(element) => element.outerHTML")
        except Exception:
            return "[unavailable]"
        compact = re.sub(r"\s+", " ", str(html)).strip()
        return compact[:limit]

    def _is_generated_file_link(
        self,
        href: str,
        download_attribute: str | None,
    ) -> bool:
        if download_attribute:
            return True

        lowered = href.lower()
        return (
            lowered.startswith("sandbox:")
            or "/mnt/data/" in lowered
            or "files.oaiusercontent.com" in lowered
            or "/backend-api/files/" in lowered
        )

    def _safe_download_filename(self, value: str) -> str:
        name = Path(value.replace("\\\\", "/")).name.strip()
        if not name or name in {".", ".."}:
            name = "generated-file"

        safe_name = re.sub(r"[^A-Za-z0-9._() -]+", "_", name)
        safe_name = safe_name.strip(" .")
        return safe_name or "generated-file"

    def _collision_safe_path(
        self,
        directory: Path,
        filename: str,
    ) -> Path:
        candidate = directory / filename
        if not candidate.exists():
            return candidate

        original = Path(filename)
        stem = original.stem or "generated-file"
        suffix = original.suffix
        counter = 2
        while True:
            candidate = directory / f"{stem}-{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _verify_requested_route(
        self,
        expected_url: str,
        observed_url: str,
    ) -> None:
        expected_id = self._conversation_id(expected_url)
        observed_id = self._conversation_id(observed_url)
        if expected_id is None:
            raise BrowserBridgeRouteMismatch(
                f"Requested route is not a verified conversation URL: "
                f"{expected_url}"
            )
        if observed_id != expected_id:
            raise BrowserBridgeRouteMismatch(
                "Dedicated page opened the wrong conversation. "
                f"Expected conversation id {expected_id}, "
                f"observed {observed_id or '[none]'}."
            )

    def _switch_to_visible_browser(self) -> None:
        self._logger.warning(
            "Switching to visible Chrome only for confirmed login or "
            "human-verification recovery"
        )
        self._report_stage(BrowserBridgeStage.HUMAN_ACTION_REQUIRED)
        self._close_dedicated_page()
        self.disconnect()
        self._terminate_owned_process()

        self._report_stage(BrowserBridgeStage.LAUNCHING_BROWSER)
        self._owned_process = ChromeLauncher(self.config).launch(headless=False)
        self._owned_process_group_id = self._owned_process.pid
        self._owned_process_is_headless = False
        self._wait_for_cdp()

    def _wait_for_visible_user_recovery(self) -> None:
        page = self.open_dedicated_page()
        page.goto(
            self.config.chatgpt_url,
            wait_until="domcontentloaded",
            timeout=int(self.config.navigation_timeout_seconds * 1000),
        )
        page.bring_to_front()
        deadline = time.monotonic() + self.config.human_action_timeout_seconds

        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            if (
                not self._human_verification_is_visible(page)
                and not self._looks_logged_out(page)
            ):
                self._close_dedicated_page()
                return
            time.sleep(1.0)

        raise BrowserBridgeTimeout(
            "Visible Chrome was opened, but login or human verification "
            "was not completed in time."
        )

    def _wait_for_cdp(self) -> None:
        deadline = time.monotonic() + self.config.browser_start_timeout_seconds
        last_error: BrowserBridgeConnectionError | None = None

        while time.monotonic() < deadline:
            if (
                self._owned_process is not None
                and self._owned_process.poll() is not None
            ):
                raise BrowserBridgeProcessExited(
                    "Chrome exited before the browser bridge could connect."
                )
            try:
                self.connect()
                return
            except BrowserBridgeConnectionError as exc:
                last_error = exc
                time.sleep(0.5)

        raise BrowserBridgeConnectionError(
            "Chrome was launched but the local CDP endpoint did not become "
            "available in time."
        ) from last_error

    def _assert_browser_alive(self) -> None:
        if (
            self._owned_process is not None
            and self._owned_process.poll() is not None
        ):
            raise BrowserBridgeProcessExited(
                "Chrome exited while Curvature Console was waiting for ChatGPT."
            )
        if self._browser is None or not self._browser.is_connected():
            raise BrowserBridgeProcessExited(
                "The browser connection closed while Curvature Console was "
                "waiting for ChatGPT."
            )

    def _assert_runtime_alive(self, page: Page) -> None:
        if self._cancel_event.is_set():
            raise BrowserBridgeCancelled(
                "Operation cancelled by the operator. No further browser action was taken."
            )
        self._assert_browser_alive()
        if page.is_closed():
            raise BrowserBridgeProcessExited(
                "The dedicated ChatGPT page closed during the request."
            )

    def _close_dedicated_page(self) -> None:
        page = self._dedicated_page
        self._dedicated_page = None
        if page is None:
            return
        try:
            if not page.is_closed():
                page.close()
        except Exception:
            pass

    def _terminate_owned_process(self) -> None:
        """Terminate the complete Chrome/Xvfb process group owned by Console.

        ``xvfb-run`` may exit while its Chrome child remains alive. Waiting on
        only the wrapper process is therefore insufficient. Every owned launch
        starts a new session, so the original wrapper PID is also the process
        group ID used to terminate all descendants.
        """

        process = self._owned_process
        process_group_id = self._owned_process_group_id
        self._owned_process = None
        self._owned_process_group_id = None
        self._owned_process_is_headless = False

        if process is None and process_group_id is None:
            return

        self._logger.info(
            "owned_process_cleanup_start pid=%s pgid=%s cdp_port=%d",
            getattr(process, "pid", None),
            process_group_id,
            self.config.debugging_port,
        )

        if process_group_id is not None:
            self._signal_owned_process_group(
                process_group_id,
                signal.SIGTERM,
            )

        if process is not None and process.poll() is None:
            try:
                process.wait(
                    timeout=self.config.process_shutdown_timeout_seconds
                )
            except subprocess.TimeoutExpired:
                pass

        if not self._wait_for_cdp_release(
            self.config.cdp_release_timeout_seconds
        ):
            self._logger.warning(
                "Owned browser did not release CDP port after SIGTERM; "
                "sending SIGKILL to process group %s",
                process_group_id,
            )
            if process_group_id is not None:
                self._signal_owned_process_group(
                    process_group_id,
                    signal.SIGKILL,
                )
            if process is not None and process.poll() is None:
                try:
                    process.wait(
                        timeout=self.config.process_shutdown_timeout_seconds
                    )
                except subprocess.TimeoutExpired:
                    self._logger.error(
                        "Owned browser wrapper did not exit after SIGKILL "
                        "pid=%s pgid=%s",
                        getattr(process, "pid", None),
                        process_group_id,
                    )

        released = self._wait_for_cdp_release(
            self.config.cdp_release_timeout_seconds
        )
        if released:
            self._logger.info(
                "owned_process_cleanup_complete cdp_port=%d released=true",
                self.config.debugging_port,
            )
        else:
            self._logger.error(
                "owned_process_cleanup_complete cdp_port=%d released=false",
                self.config.debugging_port,
            )

    def _signal_owned_process_group(
        self,
        process_group_id: int,
        signal_number: int,
    ) -> None:
        try:
            os.killpg(process_group_id, signal_number)
        except ProcessLookupError:
            return
        except PermissionError:
            self._logger.exception(
                "Cannot signal owned process group pgid=%s signal=%s",
                process_group_id,
                signal_number,
            )

    def _wait_for_cdp_release(self, timeout_seconds: float) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if not self._cdp_port_is_open():
                return True
            time.sleep(0.1)
        return not self._cdp_port_is_open()

    def _cdp_port_is_open(self) -> bool:
        try:
            with socket.create_connection(
                (
                    self.config.debugging_host,
                    self.config.debugging_port,
                ),
                timeout=0.2,
            ):
                return True
        except OSError:
            return False

    def _wait_for_message_editor(self, page: Page) -> Locator:
        deadline = time.monotonic() + self.config.editor_timeout_seconds
        last_diagnostics: list[str] = []

        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)
            if self._looks_logged_out(page):
                raise BrowserBridgeLoginRequired(
                    "The dedicated Chrome profile is not logged in to ChatGPT."
                )

            diagnostics: list[str] = []
            for selector in MESSAGE_EDITOR_SELECTORS:
                locator = page.locator(selector)
                count = locator.count()
                diagnostics.append(f"{selector}:count={count}")
                for index in range(count):
                    candidate = locator.nth(index)
                    try:
                        visible = candidate.is_visible()
                        enabled = candidate.is_enabled()
                        editable = candidate.is_editable()
                        diagnostics.append(
                            f"{selector}[{index}]:visible={visible},"
                            f"enabled={enabled},editable={editable}"
                        )
                        if visible and enabled and editable:
                            self._logger.info(
                                "editor_found request_id=%s selector=%s "
                                "index=%d",
                                self._active_request.request_id
                                if self._active_request is not None
                                else "-",
                                selector,
                                index,
                            )
                            return candidate
                    except Exception as exc:
                        diagnostics.append(
                            f"{selector}[{index}]:error={type(exc).__name__}"
                        )
            last_diagnostics = diagnostics
            time.sleep(0.25)

        self._logger.error(
            "editor_unavailable request_id=%s page_url=%s title=%r "
            "diagnostics=%s",
            self._active_request.request_id
            if self._active_request is not None
            else "-",
            page.url,
            self._safe_page_title(page),
            " | ".join(last_diagnostics),
        )
        raise BrowserBridgeEditorUnavailable(
            "ChatGPT did not expose one editable message composer. "
            "Visible Chrome was not opened because no login or human "
            "verification requirement was detected. Check the runtime log."
        )

    def _safe_page_title(self, page: Page) -> str:
        try:
            return page.title()
        except Exception:
            return "[unavailable]"

    def _wait_for_confirmed_user_message(
        self,
        page: Page,
        baseline_count: int,
        expected_text: str,
        confirmation_marker: str | None = None,
        baseline_assistant_count: int | None = None,
    ) -> None:
        """Confirm a successful submit despite ChatGPT DOM virtualisation.

        ChatGPT may keep the same number of rendered user turns after a new
        message is sent, replacing an older virtualised turn instead of
        increasing the locator count. The bridge therefore searches every
        currently rendered user turn for the unique request marker. A newly
        rendered assistant turn is also accepted as conclusive evidence that
        ChatGPT received the request.
        """

        deadline = (
            time.monotonic()
            + self.config.message_confirmation_timeout_seconds
        )
        expected_normalized = self._normalize_message_text(expected_text)
        last_observed_excerpt = ""

        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)
            if baseline_assistant_count is not None:
                current_assistant_count = page.locator(
                    ASSISTANT_MESSAGE_SELECTOR
                ).count()
                if current_assistant_count > baseline_assistant_count:
                    self._logger.info(
                        "user_message_confirmed request_id=%s "
                        "assistant_count=%d method=new_assistant_turn",
                        self._active_request.request_id
                        if self._active_request is not None
                        else "-",
                        current_assistant_count,
                    )
                    return

            messages = page.locator(USER_MESSAGE_SELECTOR)
            current_count = messages.count()

            if confirmation_marker:
                for index in range(current_count - 1, -1, -1):
                    observed_text = messages.nth(index).inner_text()
                    if confirmation_marker in observed_text:
                        self._logger.info(
                            "user_message_confirmed request_id=%s "
                            "user_count=%d marker=%s method=marker_scan",
                            self._active_request.request_id
                            if self._active_request is not None
                            else "-",
                            current_count,
                            confirmation_marker,
                        )
                        return
                    if index == current_count - 1:
                        last_observed_excerpt = (
                            self._normalize_message_text(observed_text)[:240]
                        )
            elif current_count > baseline_count:
                observed_text = messages.nth(current_count - 1).inner_text()
                observed_normalized = self._normalize_message_text(
                    observed_text
                )
                last_observed_excerpt = observed_normalized[:240]
                if observed_normalized == expected_normalized:
                    self._logger.info(
                        "user_message_confirmed request_id=%s "
                        "user_count=%d method=exact_text",
                        self._active_request.request_id
                        if self._active_request is not None
                        else "-",
                        current_count,
                    )
                    return

            time.sleep(self.config.response_poll_interval_seconds)

        if last_observed_excerpt:
            raise BrowserBridgeMessageNotConfirmed(
                "A rendered user message did not contain the current request "
                "marker before the confirmation timeout. Last rendered user "
                f"message begins with: {last_observed_excerpt!r}"
            )
        raise BrowserBridgeMessageNotConfirmed(
            "ChatGPT did not confirm the current request as a new user message."
        )

    def _assistant_message_signatures(
        self,
        page: Page,
    ) -> tuple[tuple[str, str], ...]:
        """Return stable identities for currently rendered assistant messages."""

        messages = page.locator(ASSISTANT_MESSAGE_SELECTOR)
        signatures: list[tuple[str, str]] = []
        for index in range(messages.count()):
            message = messages.nth(index)
            try:
                message_id = message.get_attribute("data-message-id") or ""
            except Exception:
                message_id = ""
            try:
                text = self._normalize_message_text(message.inner_text())
            except Exception:
                text = ""
            signatures.append((message_id, text))
        return tuple(signatures)

    def _wait_for_completed_response(
        self,
        page: Page,
        baseline_count: int,
        baseline_signatures: tuple[tuple[str, str], ...] | None = None,
    ) -> str:
        started_at = time.monotonic()
        deadline = started_at + self.config.response_timeout_seconds
        hard_deadline = (
            deadline + self.config.response_generation_grace_seconds
        )
        wait_extended = False
        stable_started_at: float | None = None
        previous_identity: tuple[str, str] | None = None
        baseline = set(baseline_signatures or ())
        baseline_ids = {message_id for message_id, _ in baseline if message_id}
        baseline_texts = {text for _, text in baseline if text}

        while time.monotonic() < hard_deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)
            messages = page.locator(ASSISTANT_MESSAGE_SELECTOR)
            current_count = messages.count()
            candidate: tuple[str, str] | None = None

            for index in range(current_count - 1, -1, -1):
                message = messages.nth(index)
                try:
                    message_id = (
                        message.get_attribute("data-message-id") or ""
                    )
                except Exception:
                    message_id = ""
                try:
                    text = message.inner_text()
                except Exception:
                    continue
                normalized_text = self._normalize_message_text(text)
                if not normalized_text:
                    continue

                is_new_identity = bool(
                    message_id and message_id not in baseline_ids
                )
                is_new_text = normalized_text not in baseline_texts
                is_count_growth_candidate = (
                    current_count > baseline_count
                    and index == current_count - 1
                )
                if (
                    is_new_identity
                    or is_new_text
                    or is_count_growth_candidate
                ):
                    candidate = (message_id, normalized_text)
                    break

            if candidate is not None:
                if candidate == previous_identity:
                    if stable_started_at is None:
                        stable_started_at = time.monotonic()
                    elif (
                        time.monotonic() - stable_started_at
                        >= self.config.stable_response_seconds
                        and not self._generation_is_active(page)
                    ):
                        self._logger.info(
                            "assistant_response_confirmed request_id=%s "
                            "message_id=%s method=identity_scan",
                            self._active_request.request_id
                            if self._active_request is not None
                            else "-",
                            candidate[0] or "-",
                        )
                        return candidate[1]
                else:
                    previous_identity = candidate
                    stable_started_at = None

            now = time.monotonic()
            if now >= deadline and not wait_extended:
                generation_active = self._generation_is_active(page)
                if generation_active or candidate is not None:
                    self._logger.info(
                        "assistant_response_wait_extended request_id=%s "
                        "reason=%s soft_timeout=%.1f hard_timeout=%.1f",
                        self._active_request.request_id
                        if self._active_request is not None
                        else "-",
                        "generation_active"
                        if generation_active
                        else "candidate_incomplete",
                        self.config.response_timeout_seconds,
                        self.config.response_timeout_seconds
                        + self.config.response_generation_grace_seconds,
                    )
                    wait_extended = True
                else:
                    break

            time.sleep(self.config.response_poll_interval_seconds)

        generation_active = self._generation_is_active(page)
        raise BrowserBridgeTimeout(
            "ChatGPT did not produce a completed assistant response in time. "
            f"Generation active at timeout: {generation_active}."
        )

    def _generation_is_active(self, page: Page) -> bool:
        candidates = (
            page.get_by_role("button", name="Stop generating"),
            page.get_by_role("button", name="Stop"),
        )
        return any(self._visible_count(candidate) > 0 for candidate in candidates)

    def _looks_logged_out(self, page: Page) -> bool:
        candidates = (
            page.get_by_role("button", name="Log in"),
            page.get_by_role("link", name="Log in"),
            page.get_by_text("Log in", exact=True),
        )
        return any(self._visible_count(candidate) > 0 for candidate in candidates)

    def _human_verification_is_visible(self, page: Page) -> bool:
        phrases = (
            "Verify you are human",
            "Checking your browser",
            "Security check",
            "Cloudflare",
            "Just a moment",
        )

        try:
            title = page.title()
        except Exception:
            title = ""

        if any(phrase.lower() in title.lower() for phrase in phrases):
            return True

        body = page.locator("body")
        if body.count() == 0:
            return False

        try:
            body_text = body.inner_text()
        except Exception:
            return False

        lowered = body_text.lower()
        return any(phrase.lower() in lowered for phrase in phrases)

    def _raise_for_human_verification(self, page: Page) -> None:
        if self._human_verification_is_visible(page):
            raise BrowserBridgeHumanVerificationRequired(
                "ChatGPT requires a visible human verification step in Chrome."
            )

    def _visible_count(self, locator: Locator) -> int:
        count = 0
        for index in range(locator.count()):
            candidate = locator.nth(index)
            try:
                if candidate.is_visible():
                    count += 1
            except Exception:
                continue
        return count

    def _conversation_id(self, value: str) -> str | None:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.netloc != "chatgpt.com":
            return None
        match = CONVERSATION_ID_PATTERN.search(parsed.path)
        return match.group(1) if match is not None else None

    def _is_conversation_url(self, value: str) -> bool:
        return self._conversation_id(value) is not None

    @staticmethod
    def _normalize_editor_equivalence(value: str) -> str:
        """Canonicalise editor text for semantic equality checks.

        ProseMirror may expose paragraph boundaries as additional newlines or
        non-breaking spaces even when the submitted text is unchanged. Raw
        character counts therefore produce false mismatches. Collapsing all
        Unicode whitespace preserves the exact token sequence while ignoring
        DOM-only paragraph formatting.
        """

        return " ".join(value.replace("\u00a0", " ").split())

    def _normalize_message_text(self, value: str) -> str:
        return "\n".join(line.rstrip() for line in value.strip().splitlines())

    def __enter__(self) -> "ChatGPTBrowserBridge":
        self.connect()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
