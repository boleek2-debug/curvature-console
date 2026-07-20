"""Background worker for one browser-mediated ChatGPT exchange."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from curvature_console.infrastructure.browser_bridge import (
    BrowserBridgeConfig,
    BrowserBridgeRouteUnverified,
    BrowserBridgeStage,
    BrowserExchangeRequest,
    ChatGPTBrowserBridge,
)


class BrowserBridgeWorker(QThread):
    """Run blocking Playwright work outside the Qt UI thread."""

    succeeded = Signal(str, str, str, str, str)
    failed = Signal(str, str)
    route_unverified = Signal(str, str, str)
    stage_changed = Signal(str, str)

    def __init__(
        self,
        config: BrowserBridgeConfig,
        request: BrowserExchangeRequest,
    ) -> None:
        super().__init__()
        self.config = config
        self.request = request

    def run(self) -> None:
        bridge = ChatGPTBrowserBridge(
            self.config,
            stage_callback=lambda stage: self.stage_changed.emit(
                self.request.department_id,
                stage.value,
            ),
        )
        result = None
        failure: Exception | None = None
        route_failure: BrowserBridgeRouteUnverified | None = None
        try:
            result = bridge.send_and_receive_hybrid(self.request)
        except BrowserBridgeRouteUnverified as exc:
            route_failure = exc
        except Exception as exc:
            failure = exc
        finally:
            bridge.close()

        if route_failure is not None:
            self.route_unverified.emit(
                self.request.department_id,
                route_failure.observed_url,
                route_failure.response_text,
            )
            return

        if failure is not None:
            self.failed.emit(self.request.department_id, str(failure))
            return

        if result is None:
            self.failed.emit(
                self.request.department_id,
                "Browser bridge ended without a result.",
            )
            return

        self.succeeded.emit(
            result.department_id,
            result.project_name,
            result.project_url,
            result.conversation_url,
            result.response_text,
        )
