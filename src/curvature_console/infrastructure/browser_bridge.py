"""Hybrid browser automation for one shared Curvature ChatGPT Project."""

from __future__ import annotations

import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse
from typing import Final

from playwright.sync_api import Browser, Locator, Page, Playwright, sync_playwright


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
MESSAGE_EDITOR_SELECTORS: Final[tuple[str, ...]] = (
    "#prompt-textarea",
    'div.ProseMirror[contenteditable="true"]',
    '[contenteditable="true"][data-virtualkeyboard="true"]',
    'textarea[placeholder*="Message"]',
)


class BrowserBridgeStage(StrEnum):
    """Visible lifecycle stages for one browser-mediated exchange."""

    CONNECTING = "Connecting"
    LAUNCHING_BROWSER = "Launching browser"
    NAVIGATING = "Navigating"
    LOCATING_EDITOR = "Locating editor"
    SENDING = "Sending"
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
    """ChatGPT did not produce a completed response in time."""


class BrowserBridgeProcessExited(BrowserBridgeError):
    """The browser process or page disappeared during an exchange."""


class BrowserBridgeEditorUnavailable(BrowserBridgeError):
    """The ChatGPT composer did not become available in the current mode."""


class BrowserBridgeRouteUnverified(BrowserBridgeError):
    """A response was received, but the observed page URL was not verified."""

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
    """Local Chrome, CDP and hybrid-runtime settings."""

    chrome_executable: Path
    profile_directory: Path
    debugging_host: str = "127.0.0.1"
    debugging_port: int = 9222
    chatgpt_url: str = "https://chatgpt.com"
    browser_start_timeout_seconds: float = 15.0
    response_timeout_seconds: float = 180.0
    response_poll_interval_seconds: float = 0.5
    stable_response_seconds: float = 2.0
    human_action_timeout_seconds: float = 300.0
    editor_timeout_seconds: float = 20.0

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
            "Response timeout": self.response_timeout_seconds,
            "Response poll interval": self.response_poll_interval_seconds,
            "Stable response duration": self.stable_response_seconds,
            "Human action timeout": self.human_action_timeout_seconds,
            "Editor timeout": self.editor_timeout_seconds,
        }
        for label, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{label} must be positive.")


@dataclass(frozen=True, slots=True)
class BrowserExchangeRequest:
    """Routing data for one browser-mediated exchange."""

    department_id: str
    message_text: str
    create_new_thread: bool
    conversation_url: str | None = None


@dataclass(frozen=True, slots=True)
class BrowserExchangeResult:
    """One completed browser-mediated ChatGPT exchange."""

    department_id: str
    project_name: str
    project_url: str
    conversation_url: str
    response_text: str


class ChromeLauncher:
    """Start ordinary Chrome in visible or headless mode."""

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
    """Exchange messages inside the shared Curvature ChatGPT Project."""

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
        """Release Playwright and every Chrome process owned by this bridge."""

        self._report_stage(BrowserBridgeStage.CLEANING_UP)
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

    def active_page(self) -> Page:
        self._assert_browser_alive()
        assert self._browser is not None
        if not self._browser.contexts:
            raise BrowserBridgeConnectionError(
                "Connected Chrome has no browser context."
            )

        context = self._browser.contexts[0]
        if not context.pages:
            return context.new_page()

        for page in context.pages:
            if "chatgpt.com" in page.url:
                return page

        return context.pages[0]

    def send_and_receive_hybrid(
        self,
        request: BrowserExchangeRequest,
    ) -> BrowserExchangeResult:
        if not request.message_text:
            raise ValueError("Message text must not be empty.")
        if not request.create_new_thread and not request.conversation_url:
            raise BrowserBridgeAmbiguousTarget(
                "No active conversation URL is stored for this department."
            )

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

    def _send_and_receive_once(
        self,
        request: BrowserExchangeRequest,
    ) -> BrowserExchangeResult:
        page = self.active_page()
        page.bring_to_front()
        self._report_stage(BrowserBridgeStage.NAVIGATING)

        target_url = (
            SHARED_PROJECT_URL
            if request.create_new_thread
            else request.conversation_url
        )
        if target_url is None:
            raise BrowserBridgeAmbiguousTarget(
                "No active conversation URL is stored for this department."
            )

        page.goto(target_url, wait_until="domcontentloaded")
        self._assert_runtime_alive(page)
        self._raise_for_human_verification(page)

        if self._looks_logged_out(page):
            raise BrowserBridgeLoginRequired(
                "The dedicated Chrome profile is not logged in to ChatGPT."
            )

        self._report_stage(BrowserBridgeStage.LOCATING_EDITOR)
        editor = self._wait_for_message_editor(page)
        assistant_messages = page.locator(ASSISTANT_MESSAGE_SELECTOR)
        baseline_count = assistant_messages.count()

        editor.fill(request.message_text)
        self._report_stage(BrowserBridgeStage.SENDING)
        editor.press("Enter")

        self._report_stage(BrowserBridgeStage.WAITING_FOR_RESPONSE)
        response_text = self._wait_for_completed_response(
            page,
            baseline_count,
        )
        self._report_stage(BrowserBridgeStage.RECEIVING)
        conversation_url = page.url

        if not self._is_conversation_url(conversation_url):
            raise BrowserBridgeRouteUnverified(
                observed_url=conversation_url,
                response_text=response_text,
            )

        self._report_stage(BrowserBridgeStage.COMPLETED)
        return BrowserExchangeResult(
            department_id=request.department_id,
            project_name=SHARED_PROJECT_NAME,
            project_url=SHARED_PROJECT_URL,
            conversation_url=conversation_url,
            response_text=response_text,
        )

    def _switch_to_visible_browser(self) -> None:
        self._report_stage(BrowserBridgeStage.HUMAN_ACTION_REQUIRED)
        self.disconnect()
        self._terminate_owned_process()

        self._report_stage(BrowserBridgeStage.LAUNCHING_BROWSER)
        self._owned_process = ChromeLauncher(self.config).launch(headless=False)
        self._owned_process_is_headless = False
        self._wait_for_cdp()
        self.active_page().bring_to_front()

    def _wait_for_visible_user_recovery(self) -> None:
        deadline = time.monotonic() + self.config.human_action_timeout_seconds

        while time.monotonic() < deadline:
            page = self.active_page()
            self._assert_runtime_alive(page)
            try:
                if "chatgpt.com" not in page.url:
                    page.goto(
                        self.config.chatgpt_url,
                        wait_until="domcontentloaded",
                    )
                if (
                    not self._human_verification_is_visible(page)
                    and not self._looks_logged_out(page)
                ):
                    return
            except BrowserBridgeProcessExited:
                raise
            except Exception:
                pass
            time.sleep(1.0)

        raise BrowserBridgeTimeout(
            "Visible Chrome was opened, but login or human verification "
            "was not completed in time."
        )

    def _wait_for_cdp(self) -> None:
        deadline = time.monotonic() + self.config.browser_start_timeout_seconds
        last_error: BrowserBridgeConnectionError | None = None

        while time.monotonic() < deadline:
            if self._owned_process is not None and self._owned_process.poll() is not None:
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
        if self._owned_process is not None and self._owned_process.poll() is not None:
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
                "The ChatGPT page closed while Curvature Console was waiting."
            )

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
            try:
                messages = page.locator(ASSISTANT_MESSAGE_SELECTOR)
                current_count = messages.count()
            except Exception as exc:
                self._assert_runtime_alive(page)
                raise BrowserBridgeProcessExited(
                    "The ChatGPT page became unavailable while waiting for "
                    "the response."
                ) from exc

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

    def _wait_for_message_editor(self, page: Page) -> Locator:
        """Wait for one supported ChatGPT composer implementation."""

        deadline = time.monotonic() + self.config.editor_timeout_seconds

        while time.monotonic() < deadline:
            self._assert_runtime_alive(page)
            self._raise_for_human_verification(page)

            if self._looks_logged_out(page):
                raise BrowserBridgeLoginRequired(
                    "The dedicated Chrome profile is not logged in to ChatGPT."
                )

            for selector in MESSAGE_EDITOR_SELECTORS:
                visible = self._visible_locators(page.locator(selector))
                if len(visible) == 1:
                    return visible[0]

            time.sleep(self.config.response_poll_interval_seconds)

        mode = "headless" if self._owned_process_is_headless else "visible"
        raise BrowserBridgeEditorUnavailable(
            "The ChatGPT message editor did not become available within "
            f"{self.config.editor_timeout_seconds:g} seconds in {mode} Chrome."
        )

    def _single_visible(
        self,
        locator: Locator,
        description: str,
    ) -> Locator:
        visible = self._visible_locators(locator)
        if len(visible) != 1:
            raise BrowserBridgeAmbiguousTarget(
                f"Expected one visible {description}, found {len(visible)}."
            )
        return visible[0]

    def _visible_count(self, locator: Locator) -> int:
        return len(self._visible_locators(locator))

    def _visible_locators(self, locator: Locator) -> list[Locator]:
        visible: list[Locator] = []
        for index in range(locator.count()):
            candidate = locator.nth(index)
            try:
                if candidate.is_visible():
                    visible.append(candidate)
            except Exception:
                continue
        return visible

    def _is_conversation_url(self, value: str) -> bool:
        """Return whether *value* is a verified ChatGPT conversation route.

        ChatGPT currently exposes both global conversation routes and
        project-scoped conversation routes. Routing is based on the URL
        itself, never on a conversation title.
        """

        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.netloc != "chatgpt.com":
            return False

        global_route = r"^/c/[0-9a-fA-F-]+/?$"
        project_route = r"^/g/g-p-[0-9a-zA-Z]+/c/[0-9a-fA-F-]+/?$"
        return bool(
            re.fullmatch(global_route, parsed.path)
            or re.fullmatch(project_route, parsed.path)
        )

    def __enter__(self) -> "ChatGPTBrowserBridge":
        self.connect()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
