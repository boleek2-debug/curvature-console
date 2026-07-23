"""Deterministic browser automation for the shared Curvature ChatGPT Project."""

from __future__ import annotations

import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

from playwright.sync_api import Browser, BrowserContext, Locator, Page, Playwright
from playwright.sync_api import sync_playwright


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
    ENTERING_MESSAGE = "Entering message"
    SENDING = "Sending"
    VERIFYING_USER_MESSAGE = "Verifying user message"
    WAITING_FOR_RESPONSE = "Waiting for response"
    RECEIVING = "Receiving"
    HUMAN_ACTION_REQUIRED = "Human action required"
    COMPLETED = "Completed"
    CLEANING_UP = "Cleaning up"


class BrowserBridgeError(RuntimeError):
    """Base class for recoverable browser-bridge failures."""


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


class BrowserBridgeRouteMismatch(BrowserBridgeError):
    """The dedicated page does not point to the requested conversation."""


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
    debugging_host: str = "127.0.0.1"
    debugging_port: int = 9222
    chatgpt_url: str = "https://chatgpt.com"
    browser_start_timeout_seconds: float = 15.0
    navigation_timeout_seconds: float = 45.0
    editor_timeout_seconds: float = 30.0
    message_confirmation_timeout_seconds: float = 30.0
    response_timeout_seconds: float = 180.0
    response_poll_interval_seconds: float = 0.5
    stable_response_seconds: float = 2.0
    human_action_timeout_seconds: float = 300.0

    @property
    def cdp_url(self) -> str:
        return f"http://{self.debugging_host}:{self.debugging_port}"

    @classmethod
    def default(cls, project_root: Path | None = None) -> "BrowserBridgeConfig":
        root = (project_root or Path.cwd()).expanduser().resolve()
        return cls(
            chrome_executable=Path("/usr/bin/google-chrome-stable"),
            profile_directory=root / "data" / "browser-profile",
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
            "Response poll interval": self.response_poll_interval_seconds,
            "Stable response duration": self.stable_response_seconds,
            "Human action timeout": self.human_action_timeout_seconds,
        }
        for label, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{label} must be positive.")


@dataclass(frozen=True, slots=True)
class BrowserExchangeRequest:
    """Immutable routing data for one browser-mediated exchange."""

    request_id: str
    department_id: str
    message_text: str
    create_new_thread: bool
    conversation_url: str | None = None


@dataclass(frozen=True, slots=True)
class BrowserExchangeResult:
    """One completed and request-bound browser exchange."""

    request_id: str
    department_id: str
    project_name: str
    project_url: str
    conversation_url: str
    response_text: str


class ChromeLauncher:
    """Start Chrome in visible or headless mode."""

    def __init__(self, config: BrowserBridgeConfig) -> None:
        self.config = config

    def command(self, *, headless: bool = False) -> tuple[str, ...]:
        self.config.validate()
        self.config.profile_directory.mkdir(parents=True, exist_ok=True)

        arguments = [
            str(self.config.chrome_executable),
            f"--remote-debugging-address={self.config.debugging_host}",
            f"--remote-debugging-port={self.config.debugging_port}",
            f"--user-data-dir={self.config.profile_directory}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        if headless:
            arguments.extend(["--headless=new", "--window-size=1440,1000"])
        arguments.append(self.config.chatgpt_url)
        return tuple(arguments)

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
        self._owned_process_is_headless = False
        self._dedicated_page: Page | None = None

    def _report_stage(self, stage: BrowserBridgeStage) -> None:
        if self._stage_callback is not None:
            self._stage_callback(stage)

    def connect(self) -> None:
        if self._browser is not None:
            return

        self._report_stage(BrowserBridgeStage.CONNECTING)
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
        self._owned_process = ChromeLauncher(self.config).launch(headless=True)
        self._owned_process_is_headless = True
        try:
            self._wait_for_cdp()
        except Exception:
            self._terminate_owned_process()
            raise

    def close(self) -> None:
        """Close only the dedicated page and processes owned by this bridge."""

        self._report_stage(BrowserBridgeStage.CLEANING_UP)
        self._close_dedicated_page()
        try:
            self.disconnect()
        finally:
            self._terminate_owned_process()

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

        try:
            return self._send_and_receive_once(request)
        except (
            BrowserBridgeLoginRequired,
            BrowserBridgeHumanVerificationRequired,
            BrowserBridgeEditorUnavailable,
        ):
            if not self._owned_process_is_headless:
                raise
            self._switch_to_visible_browser()
            self._wait_for_visible_user_recovery()
            return self._send_and_receive_once(request)

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

        transport_text = self._transport_message_text(request)

        self._report_stage(BrowserBridgeStage.ENTERING_MESSAGE)
        editor.fill(
            transport_text,
            timeout=int(self.config.editor_timeout_seconds * 1000),
        )
        self._report_stage(BrowserBridgeStage.SENDING)
        editor.press("Enter")

        self._report_stage(BrowserBridgeStage.VERIFYING_USER_MESSAGE)
        self._wait_for_confirmed_user_message(
            page=page,
            baseline_count=baseline_user_count,
            request_id=request.request_id,
        )

        self._report_stage(BrowserBridgeStage.WAITING_FOR_RESPONSE)
        response_text = self._wait_for_completed_response(
            page=page,
            baseline_count=baseline_assistant_count,
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

        self._report_stage(BrowserBridgeStage.COMPLETED)
        return BrowserExchangeResult(
            request_id=request.request_id,
            department_id=request.department_id,
            project_name=SHARED_PROJECT_NAME,
            project_url=SHARED_PROJECT_URL,
            conversation_url=conversation_url,
            response_text=response_text,
        )

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
        self._report_stage(BrowserBridgeStage.HUMAN_ACTION_REQUIRED)
        self._close_dedicated_page()
        self.disconnect()
        self._terminate_owned_process()

        self._report_stage(BrowserBridgeStage.LAUNCHING_BROWSER)
        self._owned_process = ChromeLauncher(self.config).launch(headless=False)
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
        process = self._owned_process
        self._owned_process = None
        self._owned_process_is_headless = False

        if process is None or process.poll() is not None:
            return

        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        time.sleep(0.5)

    def _wait_for_message_editor(self, page: Page) -> Locator:
        deadline = time.monotonic() + self.config.editor_timeout_seconds
        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)
            if self._looks_logged_out(page):
                raise BrowserBridgeLoginRequired(
                    "The dedicated Chrome profile is not logged in to ChatGPT."
                )

            for selector in MESSAGE_EDITOR_SELECTORS:
                locator = page.locator(selector)
                for index in range(locator.count()):
                    candidate = locator.nth(index)
                    try:
                        if (
                            candidate.is_visible()
                            and candidate.is_enabled()
                            and candidate.is_editable()
                        ):
                            return candidate
                    except Exception:
                        continue
            time.sleep(0.25)

        raise BrowserBridgeEditorUnavailable(
            "ChatGPT did not expose one editable message composer."
        )

    def _wait_for_confirmed_user_message(
        self,
        page: Page,
        baseline_count: int,
        request_id: str,
    ) -> None:
        """Confirm the sent request by its unique visible transport marker.

        ChatGPT renders Markdown and rich text differently from the composer,
        so comparing the complete editor payload with rendered ``inner_text``
        is not reliable. The immutable request id is the deterministic
        correlation key.
        """

        deadline = (
            time.monotonic()
            + self.config.message_confirmation_timeout_seconds
        )
        marker = self._request_marker(request_id)

        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)
            messages = page.locator(USER_MESSAGE_SELECTOR)
            current_count = messages.count()

            if current_count > baseline_count:
                observed_text = messages.nth(current_count - 1).inner_text()
                if marker in observed_text:
                    return
                raise BrowserBridgeMessageNotConfirmed(
                    "A new user message appeared, but it did not contain the "
                    "current request marker."
                )
            time.sleep(self.config.response_poll_interval_seconds)

        raise BrowserBridgeMessageNotConfirmed(
            "ChatGPT did not confirm the current request as a new user message."
        )

    def _transport_message_text(
        self,
        request: BrowserExchangeRequest,
    ) -> str:
        """Add a visible correlation marker without changing package content."""

        return (
            f"{self._request_marker(request.request_id)}\n\n"
            f"{request.message_text.strip()}\n"
        )

    def _request_marker(self, request_id: str) -> str:
        return f"CURVATURE_REQUEST_ID: {request_id}"

    def _wait_for_completed_response(
        self,
        page: Page,
        baseline_count: int,
    ) -> str:
        deadline = time.monotonic() + self.config.response_timeout_seconds
        stable_started_at: float | None = None
        previous_text: str | None = None

        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)
            messages = page.locator(ASSISTANT_MESSAGE_SELECTOR)
            current_count = messages.count()

            if current_count > baseline_count:
                latest = messages.nth(current_count - 1)
                text = latest.inner_text()

                if text and text == previous_text:
                    if stable_started_at is None:
                        stable_started_at = time.monotonic()
                    elif (
                        time.monotonic() - stable_started_at
                        >= self.config.stable_response_seconds
                        and not self._generation_is_active(page)
                    ):
                        return text
                else:
                    previous_text = text
                    stable_started_at = None

            time.sleep(self.config.response_poll_interval_seconds)

        raise BrowserBridgeTimeout(
            "ChatGPT did not produce a completed assistant response in time."
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
        )
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

    def _normalize_message_text(self, value: str) -> str:
        return "\n".join(line.rstrip() for line in value.strip().splitlines())

    def __enter__(self) -> "ChatGPTBrowserBridge":
        self.connect()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
