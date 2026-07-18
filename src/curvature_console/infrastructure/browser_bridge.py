"""Browser automation foundation for official ChatGPT Projects."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from playwright.sync_api import Browser, Page, Playwright, sync_playwright


DEPARTMENT_PROJECT_NAMES: Final[dict[str, str]] = {
    "project": "Curvature Project",
    "core": "Curvature Core",
    "research": "Curvature Research",
}


@dataclass(frozen=True, slots=True)
class BrowserBridgeConfig:
    """Local Chrome and CDP settings for the browser bridge."""

    chrome_executable: Path
    profile_directory: Path
    debugging_host: str = "127.0.0.1"
    debugging_port: int = 9222
    chatgpt_url: str = "https://chatgpt.com"

    @property
    def cdp_url(self) -> str:
        """Return the Chrome DevTools Protocol endpoint."""

        return f"http://{self.debugging_host}:{self.debugging_port}"

    @classmethod
    def default(cls, project_root: Path | None = None) -> "BrowserBridgeConfig":
        """Return the default local Linux configuration."""

        root = (project_root or Path.cwd()).expanduser().resolve()
        return cls(
            chrome_executable=Path("/usr/bin/google-chrome-stable"),
            profile_directory=root / "data" / "browser-profile",
        )

    def validate(self) -> None:
        """Validate local paths and network settings."""

        if not self.chrome_executable.is_file():
            raise FileNotFoundError(
                f"Chrome executable not found: {self.chrome_executable}"
            )
        if not 1 <= self.debugging_port <= 65535:
            raise ValueError("Debugging port must be between 1 and 65535.")


@dataclass(frozen=True, slots=True)
class BrowserBridgeStatus:
    """Read-only status returned by a bridge probe."""

    connected: bool
    logged_in: bool
    page_title: str
    page_url: str
    visible_project_names: tuple[str, ...]


class ChromeLauncher:
    """Start ordinary Chrome with a persistent local profile and CDP enabled."""

    def __init__(self, config: BrowserBridgeConfig) -> None:
        self.config = config

    def command(self) -> tuple[str, ...]:
        """Return the exact Chrome command without launching it."""

        self.config.validate()
        self.config.profile_directory.mkdir(parents=True, exist_ok=True)

        return (
            str(self.config.chrome_executable),
            f"--remote-debugging-port={self.config.debugging_port}",
            f"--user-data-dir={self.config.profile_directory}",
            "--no-first-run",
            "--no-default-browser-check",
            self.config.chatgpt_url,
        )

    def launch(self) -> subprocess.Popen[bytes]:
        """Launch ordinary Chrome detached from Console."""

        return subprocess.Popen(
            self.command(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


class ChatGPTBrowserBridge:
    """Connect to a logged-in Chrome instance through CDP."""

    def __init__(self, config: BrowserBridgeConfig) -> None:
        self.config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def connect(self) -> None:
        """Connect to the already-running Chrome instance."""

        if self._browser is not None:
            return

        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.connect_over_cdp(
                self.config.cdp_url
            )
        except Exception:
            self._playwright.stop()
            self._playwright = None
            raise

    def disconnect(self) -> None:
        """Release Playwright without terminating ordinary Chrome."""

        if self._playwright is not None:
            self._playwright.stop()

        self._browser = None
        self._playwright = None

    def active_page(self) -> Page:
        """Return the current controlled ChatGPT page."""

        if self._browser is None:
            raise RuntimeError("Browser bridge is not connected.")
        if not self._browser.contexts:
            raise RuntimeError("Connected Chrome has no browser context.")

        context = self._browser.contexts[0]
        if not context.pages:
            return context.new_page()

        return context.pages[0]

    def probe(self) -> BrowserBridgeStatus:
        """Inspect login state and known Curvature Projects."""

        page = self.active_page()
        page.bring_to_front()

        visible_projects = tuple(
            project_name
            for project_name in DEPARTMENT_PROJECT_NAMES.values()
            if page.get_by_text(project_name, exact=True).count() > 0
        )

        logged_in = page.get_by_text("Projects", exact=True).count() > 0

        return BrowserBridgeStatus(
            connected=True,
            logged_in=logged_in,
            page_title=page.title(),
            page_url=page.url,
            visible_project_names=visible_projects,
        )

    def project_name_for_department(self, department_id: str) -> str:
        """Return the official ChatGPT Project mapped to one department."""

        try:
            return DEPARTMENT_PROJECT_NAMES[department_id]
        except KeyError as exc:
            raise ValueError(
                f"Unknown department: {department_id}"
            ) from exc

    def __enter__(self) -> "ChatGPTBrowserBridge":
        self.connect()
        return self

    def __exit__(self, *_args: object) -> None:
        self.disconnect()
