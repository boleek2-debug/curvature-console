"""Main three-panel desktop window for Curvature Console."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QToolBar,
    QWidget,
)

from curvature_console.configuration.workspace_config import (
    WorkspaceConfig,
    WorkspaceConfigError,
    load_workspace_config,
)
from curvature_console.infrastructure.browser_bridge import (
    BOOTSTRAP_CONVERSATION_URLS,
    SHARED_PROJECT_NAME,
    SHARED_PROJECT_URL,
    BrowserBridgeConfig,
    BrowserExchangeRequest,
)
from curvature_console.infrastructure.context_loader import (
    ContextLoadResult,
    WorkspaceContextLoader,
)
from curvature_console.infrastructure.package_apply import PackageApplier
from curvature_console.infrastructure.package_review import (
    PackageReviewError,
    PackageReviewer,
)
from curvature_console.infrastructure.state_store import SQLiteStateStore
from curvature_console.infrastructure.transfer_package import (
    TransferPackage,
    TransferPackageBuilder,
    TransferPackageMode,
    TransferPackageRequest,
)
from curvature_console.presentation.browser_bridge_worker import (
    BrowserBridgeWorker,
)
from curvature_console.presentation.context_preview_dialog import (
    ContextPreviewDialog,
)
from curvature_console.presentation.department_panel import DepartmentPanel
from curvature_console.presentation.package_review_dialog import (
    PackageReviewDialog,
)


@dataclass(frozen=True, slots=True)
class PendingBrowserExchange:
    """UI state belonging to exactly one immutable browser request."""

    request_id: str
    department_id: str
    user_task: str
    mode: TransferPackageMode = TransferPackageMode.TASK


class MainWindow(QMainWindow):
    """Display Project, Core and Research simultaneously."""

    DEPARTMENT_DEFINITIONS = (
        (
            "project",
            "Curvature Project",
            "Direction, priorities, milestone approval and arbitration.",
        ),
        (
            "core",
            "Curvature Core",
            "Architecture, implementation, validation, persistence and tests.",
        ),
        (
            "research",
            "Curvature Research",
            "Sources, evidence, hypotheses, confidence and research graph.",
        ),
    )

    def __init__(
        self,
        application_name: str = "Curvature Console",
        config_directory: Path | None = None,
        state_path: Path | None = None,
        data_directory: Path | None = None,
        browser_config: BrowserBridgeConfig | None = None,
        repository_roots: dict[str, Path] | None = None,
        package_backup_root: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(application_name)
        self.resize(1500, 850)

        self.config_directory = (
            config_directory
            if config_directory is not None
            else Path.cwd() / "config" / "workspaces"
        )
        self.data_directory = (
            data_directory
            if data_directory is not None
            else Path.cwd() / "data"
        )
        self.browser_config = browser_config or BrowserBridgeConfig.default(
            Path.cwd()
        )
        self.repository_roots = {
            key: value.expanduser().resolve()
            for key, value in (
                repository_roots
                or {
                    "curvature-console": Path.cwd(),
                    "Curvature": Path("~/Curvature"),
                }
            ).items()
        }
        self.package_reviewer = PackageReviewer()
        self.package_applier = PackageApplier(
            reviewer=self.package_reviewer,
            backup_root=package_backup_root,
        )
        self.state_store = SQLiteStateStore(state_path)
        self._bootstrap_chat_routes()
        self.context_loader = WorkspaceContextLoader()
        self.transfer_package_builder = TransferPackageBuilder()
        self.workspace_configs: dict[str, WorkspaceConfig] = {}
        self.context_results: dict[str, ContextLoadResult] = {}

        self._restoring_state = True
        self._focused_department_id: str | None = None
        self._three_panel_sizes = [500, 500, 500]
        self._browser_worker: BrowserBridgeWorker | None = None
        self._pending_exchanges: dict[str, PendingBrowserExchange] = {}

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("departmentSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.splitterMoved.connect(self._save_layout_state)

        self.department_panels: dict[str, DepartmentPanel] = {}

        for department_id, title, responsibility in self.DEPARTMENT_DEFINITIONS:
            panel = DepartmentPanel(
                department_id=department_id,
                title=title,
                responsibility=responsibility,
                attachment_storage_dir=(
                    self.data_directory / "attachments" / department_id
                ),
            )
            panel.focus_requested.connect(self.focus_department)
            panel.context_refresh_requested.connect(self.refresh_context)
            panel.context_preview_requested.connect(self.preview_context)
            panel.transfer_package_requested.connect(
                self.prepare_transfer_package
            )
            panel.package_review_requested.connect(
                self.review_generated_package
            )
            panel.workspace_state_changed.connect(self.save_department_state)
            self.department_panels[department_id] = panel
            self.splitter.addWidget(panel)

        self.splitter.setSizes(self._three_panel_sizes)
        self.setCentralWidget(self.splitter)

        self.restore_button = QPushButton("Show All Departments")
        self.restore_button.setObjectName("restoreThreePanelButton")
        self.restore_button.clicked.connect(self.restore_three_panel_view)
        self.restore_button.setEnabled(False)

        self.refresh_all_button = QPushButton("Refresh All Context")
        self.refresh_all_button.setObjectName("refreshAllContextButton")
        self.refresh_all_button.clicked.connect(self.refresh_all_contexts)

        toolbar = QToolBar("Workspace")
        toolbar.setObjectName("workspaceToolbar")
        toolbar.setMovable(False)
        toolbar.addWidget(self.restore_button)
        toolbar.addWidget(self.refresh_all_button)
        self.addToolBar(toolbar)

        status_bar = QStatusBar()
        status_bar.setObjectName("applicationStatusBar")
        status_bar.showMessage(
            "Three departments operational — ChatGPT browser bridge ready"
        )
        self.setStatusBar(status_bar)

        self.load_workspace_configs()
        self.refresh_all_contexts()
        self.restore_persisted_state()
        self._restoring_state = False

    def _bootstrap_chat_routes(self) -> None:
        """Initialise missing department routes without using chat titles."""

        for department_id, conversation_url in (
            BOOTSTRAP_CONVERSATION_URLS.items()
        ):
            if self.state_store.load_chat_route(department_id) is not None:
                continue
            self.state_store.save_chat_route(
                department_id=department_id,
                project_name=SHARED_PROJECT_NAME,
                project_url=SHARED_PROJECT_URL,
                active_conversation_url=conversation_url,
            )

    @property
    def focused_department_id(self) -> str | None:
        """Return the currently focused department, if any."""
        return self._focused_department_id

    def load_workspace_configs(self) -> None:
        """Load all three workspace configuration files."""

        loaded: dict[str, WorkspaceConfig] = {}

        for department_id in self.department_panels:
            path = self.config_directory / f"{department_id}.yaml"

            try:
                config = load_workspace_config(path)
            except WorkspaceConfigError as exc:
                self.statusBar().showMessage(str(exc))
                continue

            if config.department_id != department_id:
                self.statusBar().showMessage(
                    f"Config department mismatch: {path}"
                )
                continue

            loaded[department_id] = config

        self.workspace_configs = loaded

    def refresh_all_contexts(self) -> None:
        """Reload context for every configured workspace."""

        for department_id in self.department_panels:
            self.refresh_context(department_id)

        loaded_total = sum(
            result.loaded_count for result in self.context_results.values()
        )
        error_total = sum(
            len(result.errors) for result in self.context_results.values()
        )
        self.statusBar().showMessage(
            f"Local context refreshed: {loaded_total} documents · "
            f"{error_total} errors"
        )

    def refresh_context(self, department_id: str) -> None:
        """Reload one department context from role and repository files."""

        config = self.workspace_configs.get(department_id)

        if config is None:
            result = ContextLoadResult(
                department_id=department_id,
                documents=(),
                errors=(f"No valid workspace config for {department_id}.",),
            )
        else:
            result = self.context_loader.load(config)

        self.context_results[department_id] = result
        self.department_panels[department_id].set_context_result(result)

    def preview_context(self, department_id: str) -> None:
        """Open a readable context preview for one department."""

        result = self.context_results.get(department_id)

        if result is None:
            QMessageBox.information(
                self,
                "Context unavailable",
                "Refresh this workspace context first.",
            )
            return

        panel = self.department_panels[department_id]
        dialog = ContextPreviewDialog(
            title=panel.title_label.text(),
            result=result,
            parent=self,
        )
        dialog.exec()

    def review_generated_package(
        self,
        department_id: str,
        package_path_value: str,
    ) -> None:
        """Open a complete read-only review for one generated ZIP."""

        if department_id not in self.department_panels:
            raise ValueError(f"Unknown department: {department_id}")

        package_path = Path(package_path_value).expanduser()
        try:
            repository_id = (
                self.package_reviewer.manifest_target_repository(
                    package_path
                )
            )
            repository_root = self.repository_roots.get(repository_id)
            if repository_root is None:
                raise PackageReviewError(
                    "No approved local repository is registered for "
                    f"package target {repository_id!r}."
                )
            review = self.package_reviewer.review(
                package_path,
                repository_id=repository_id,
                repository_root=repository_root,
            )
        except PackageReviewError as exc:
            QMessageBox.critical(
                self,
                "Package review failed",
                str(exc),
            )
            return

        dialog = PackageReviewDialog(
            review=review,
            apply_callback=self.package_applier.apply,
            parent=self,
        )
        dialog.exec()
        state = (
            "eligible"
            if review.is_apply_eligible
            else "blocked by conflicts"
        )
        self.statusBar().showMessage(
            f"Package reviewed for {department_id}: {state}"
        )

    def prepare_transfer_package(
        self,
        department_id: str,
        mode_value: str,
    ) -> None:
        """Build and send a task, confirming only a new-thread handoff."""

        if self._browser_worker is not None:
            QMessageBox.information(
                self,
                "ChatGPT operation in progress",
                "Wait for the current ChatGPT response before sending another "
                "package.",
            )
            return

        package = self._build_transfer_package(department_id, mode_value)
        if package is None:
            return

        panel = self.department_panels[department_id]
        pressure = panel.thread_pressure_snapshot

        if (
            package.mode is TransferPackageMode.TASK
            and pressure.should_avoid_regular_task
        ):
            answer = QMessageBox.warning(
                self,
                "Thread pressure is RED",
                "The local thread-pressure estimate is RED. A Thread "
                "Handoff is strongly recommended before more work.\n\n"
                "Send this regular task anyway?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        if package.mode is TransferPackageMode.THREAD_HANDOFF:
            answer = QMessageBox.warning(
                self,
                "Start a new ChatGPT thread?",
                "This Thread Handoff will start a NEW ChatGPT conversation "
                f"for {panel.title_label.text()}. The current conversation "
                "will remain unchanged.",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.start_browser_exchange(package)

    def start_browser_exchange(self, package: TransferPackage) -> None:
        """Start one immutable request with its own request identifier."""

        department_id = package.department_id
        panel = self.department_panels[department_id]
        request_id = uuid4().hex
        pending = PendingBrowserExchange(
            request_id=request_id,
            department_id=department_id,
            user_task=panel.input_editor.toPlainText(),
            mode=package.mode,
        )
        self._pending_exchanges[request_id] = pending
        self._set_browser_operation_busy(True, department_id)
        self.statusBar().showMessage(
            f"Sending {package.mode.display_name} to "
            f"{panel.title_label.text()}..."
        )

        route = self.state_store.load_chat_route(department_id)
        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id,
                department_id=department_id,
                message_text=package.text,
                create_new_thread=(
                    package.mode is TransferPackageMode.THREAD_HANDOFF
                ),
                conversation_url=(
                    route.active_conversation_url
                    if route is not None
                    else None
                ),
                attachment_paths=tuple(
                    record.path
                    for record in panel.attachment_list.records
                ),
            ),
        )
        worker.succeeded.connect(self._handle_browser_success)
        worker.failed.connect(self._handle_browser_failure)
        worker.route_unverified.connect(
            self._handle_browser_route_unverified
        )
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self._browser_worker = worker
        worker.start()

    def _pending_exchange(
        self,
        request_id: str,
        department_id: str,
    ) -> PendingBrowserExchange | None:
        pending = self._pending_exchanges.get(request_id)
        if pending is None or pending.department_id != department_id:
            return None
        return pending

    def _handle_browser_success(
        self,
        request_id: str,
        department_id: str,
        project_name: str,
        project_url: str,
        conversation_url: str,
        response_text: str,
        downloads: object = (),
    ) -> None:
        pending = self._pending_exchange(request_id, department_id)
        if pending is None:
            return

        self._pending_exchanges.pop(request_id, None)
        panel = self.department_panels[department_id]
        if pending.mode is TransferPackageMode.THREAD_HANDOFF:
            panel.start_new_thread_exchange(
                pending.user_task,
                response_text,
            )
        else:
            panel.append_browser_exchange(pending.user_task, response_text)
        self.state_store.save_generated_downloads(
            request_id=request_id,
            department_id=department_id,
            conversation_url=conversation_url,
            downloads=tuple(downloads),
        )
        panel.set_generated_downloads(
            self.state_store.load_generated_downloads(department_id)
        )
        self.state_store.save_chat_route(
            department_id=department_id,
            project_name=project_name,
            project_url=project_url,
            active_conversation_url=conversation_url,
        )
        panel.input_editor.clear()
        self._set_browser_operation_busy(False, department_id)
        self.save_department_state(department_id)
        self.statusBar().showMessage(
            f"ChatGPT response received and saved: "
            f"{panel.title_label.text()}"
        )

    def _handle_browser_route_unverified(
        self,
        request_id: str,
        department_id: str,
        observed_url: str,
        response_text: str,
        downloads: object = (),
    ) -> None:
        """Preserve only the response belonging to the current request."""

        pending = self._pending_exchange(request_id, department_id)
        if pending is None:
            return

        self._pending_exchanges.pop(request_id, None)
        panel = self.department_panels[department_id]
        panel.append_browser_exchange(pending.user_task, response_text)
        route = self.state_store.load_chat_route(department_id)
        conversation_url = (
            route.active_conversation_url
            if route is not None
            else observed_url
        )
        self.state_store.save_generated_downloads(
            request_id=request_id,
            department_id=department_id,
            conversation_url=conversation_url,
            downloads=tuple(downloads),
        )
        panel.set_generated_downloads(
            self.state_store.load_generated_downloads(department_id)
        )
        panel.input_editor.clear()
        self._set_browser_operation_busy(False, department_id)
        self.save_department_state(department_id)
        self.statusBar().showMessage(
            f"ChatGPT response saved; route requires verification: "
            f"{panel.title_label.text()}"
        )
        QMessageBox.warning(
            self,
            "ChatGPT route requires verification",
            "The response was received and saved, but the active "
            "conversation route was not changed.\n\n"
            f"Observed page URL:\n{observed_url}",
        )

    def _handle_browser_failure(
        self,
        request_id: str,
        department_id: str,
        error_message: str,
    ) -> None:
        pending = self._pending_exchange(request_id, department_id)
        if pending is None:
            return

        self._pending_exchanges.pop(request_id, None)
        panel = self.department_panels[department_id]
        self._set_browser_operation_busy(False, department_id)
        self.statusBar().showMessage(
            f"ChatGPT browser operation failed: {panel.title_label.text()}"
        )
        QMessageBox.critical(
            self,
            "ChatGPT browser bridge failed",
            error_message,
        )

    def _handle_browser_stage(
        self,
        request_id: str,
        department_id: str,
        stage: str,
    ) -> None:
        if self._pending_exchange(request_id, department_id) is None:
            return

        panel = self.department_panels[department_id]
        panel.set_browser_stage(stage)
        self.statusBar().showMessage(
            f"{panel.title_label.text()}: {stage}"
        )

    def _set_browser_operation_busy(

        self,
        busy: bool,
        active_department_id: str | None = None,
    ) -> None:
        """Lock only the department currently using the browser bridge."""

        if active_department_id is None:
            return

        panel = self.department_panels[active_department_id]
        panel.set_browser_busy(busy)

    def _clear_browser_worker(self) -> None:
        worker = self._browser_worker
        self._browser_worker = None
        if worker is not None:
            worker.deleteLater()

    def _build_transfer_package(
        self,
        department_id: str,
        mode_value: str,
    ) -> TransferPackage | None:
        if department_id not in self.department_panels:
            raise ValueError(f"Unknown department: {department_id}")

        result = self.context_results.get(department_id)
        if result is None:
            QMessageBox.information(
                self,
                "Context unavailable",
                "Refresh this workspace context before preparing a package.",
            )
            return None

        panel = self.department_panels[department_id]
        try:
            mode = TransferPackageMode(mode_value)
        except ValueError as exc:
            raise ValueError(
                f"Unknown transfer package mode: {mode_value}"
            ) from exc

        return self.transfer_package_builder.build(
            TransferPackageRequest(
                mode=mode,
                department_id=department_id,
                department_title=panel.title_label.text(),
                responsibility=panel.responsibility,
                context=result,
                conversation_text=panel.conversation_view.toPlainText(),
                draft_text=panel.input_editor.toPlainText(),
                attachments=panel.attachment_list.records,
            )
        )

    def restore_persisted_state(self) -> None:
        """Restore department content, attachments and layout."""

        for department_id, panel in self.department_panels.items():
            state = self.state_store.load_department_state(department_id)
            if state is not None:
                panel.conversation_view.setPlainText(state.conversation_text)
                panel.input_editor.setPlainText(state.draft_text)

            panel.attachment_list.restore_records(
                self.state_store.load_attachments(department_id)
            )
            panel.set_generated_downloads(
                self.state_store.load_generated_downloads(department_id)
            )

        layout = self.state_store.load_layout()
        if layout is None:
            return

        self._three_panel_sizes = list(layout.splitter_sizes)
        self.splitter.setSizes(self._three_panel_sizes)

        if layout.focused_department_id is not None:
            self.focus_department(
                layout.focused_department_id,
                capture_current_sizes=False,
            )

    def save_department_state(self, department_id: str) -> None:
        """Persist one department workspace immediately."""

        if self._restoring_state:
            return

        panel = self.department_panels[department_id]
        self.state_store.save_department_state(
            department_id=department_id,
            conversation_text=panel.conversation_view.toPlainText(),
            draft_text=panel.input_editor.toPlainText(),
        )
        self.state_store.replace_attachments(
            department_id,
            panel.attachment_list.records,
        )

    def save_all_state(self) -> None:
        """Persist every department and the current layout."""

        for department_id in self.department_panels:
            self.save_department_state(department_id)
        self._save_layout_state()

    def focus_department(
        self,
        department_id: str,
        capture_current_sizes: bool = True,
    ) -> None:
        """Temporarily show one department without destroying other state."""

        if department_id not in self.department_panels:
            raise ValueError(f"Unknown department: {department_id}")

        if self._focused_department_id is None and capture_current_sizes:
            current_sizes = self.splitter.sizes()
            if current_sizes and any(current_sizes):
                self._three_panel_sizes = current_sizes

        for current_id, panel in self.department_panels.items():
            panel.setVisible(current_id == department_id)

        self._focused_department_id = department_id
        self.restore_button.setEnabled(True)
        self.statusBar().showMessage(
            f"Focused: {self.department_panels[department_id].title_label.text()}"
        )
        self._save_layout_state()

    def restore_three_panel_view(self) -> None:
        """Restore all three department panels and their previous widths."""

        for panel in self.department_panels.values():
            panel.setVisible(True)

        self._focused_department_id = None
        self.splitter.setSizes(self._three_panel_sizes)
        self.restore_button.setEnabled(False)
        self.statusBar().showMessage(
            "Three departments operational — ChatGPT browser bridge ready"
        )
        self._save_layout_state()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Persist operational state before closing."""

        if self._browser_worker is not None:
            QMessageBox.information(
                self,
                "ChatGPT operation in progress",
                "Wait for the current ChatGPT response before closing "
                "Curvature Console.",
            )
            event.ignore()
            return

        self.save_all_state()
        self.state_store.close()
        super().closeEvent(event)

    def _save_layout_state(self, *_args) -> None:
        if self._restoring_state:
            return

        if self._focused_department_id is None:
            sizes = self.splitter.sizes()
            if len(sizes) == 3 and any(sizes):
                self._three_panel_sizes = sizes

        self.state_store.save_layout(
            self._three_panel_sizes,
            self._focused_department_id,
        )
