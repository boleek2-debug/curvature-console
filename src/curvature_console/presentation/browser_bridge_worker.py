"""Background worker for one deterministic ChatGPT exchange."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from curvature_console.infrastructure.runtime_logging import (
    get_runtime_logger,
)
from curvature_console.infrastructure.browser_bridge import (
    BrowserBridgeConfig,
    BrowserBridgeRouteUnverified,
    BrowserBridgeStage,
    BrowserExchangeRequest,
    ChatGPTBrowserBridge,
)


class BrowserBridgeWorker(QThread):
    """Run one immutable request outside the Qt UI thread."""

    succeeded = Signal(str, str, str, str, str, str)
    failed = Signal(str, str, str)
    route_unverified = Signal(str, str, str, str)
    stage_changed = Signal(str, str, str)

    def __init__(
        self,
        config: BrowserBridgeConfig,
        request: BrowserExchangeRequest,
    ) -> None:
        super().__init__()
        self.config = config
        self.request = request

    def run(self) -> None:
        logger = get_runtime_logger("browser_bridge_worker")
        logger.info(
            "worker_start request_id=%s department_id=%s",
            self.request.request_id,
            self.request.department_id,
        )
        bridge = ChatGPTBrowserBridge(
            self.config,
            stage_callback=lambda stage: self.stage_changed.emit(
                self.request.request_id,
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
            logger.exception(
                "worker_failure request_id=%s department_id=%s",
                self.request.request_id,
                self.request.department_id,
            )
        finally:
            bridge.close()

        if route_failure is not None:
            self.route_unverified.emit(
                self.request.request_id,
                self.request.department_id,
                route_failure.observed_url,
                route_failure.response_text,
            )
            return

        if failure is not None:
            self.failed.emit(
                self.request.request_id,
                self.request.department_id,
                str(failure),
            )
            return

        logger.info(
            "worker_finished request_id=%s department_id=%s",
            self.request.request_id,
            self.request.department_id,
        )

        if result is None:
            self.failed.emit(
                self.request.request_id,
                self.request.department_id,
                "Browser bridge ended without a result.",
            )
            return

        self.succeeded.emit(
            result.request_id,
            result.department_id,
            result.project_name,
            result.project_url,
            result.conversation_url,
            result.response_text,
        )
