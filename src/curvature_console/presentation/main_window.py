"""Main three-panel desktop window for Curvature Console."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
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
from curvature_console.infrastructure.package_apply import PackageApplier
from curvature_console.infrastructure.package_review import (
    PackageReviewError,
    PackageReviewer,
)
from curvature_console.infrastructure.context_loader import (
    ContextLoadResult,
    WorkspaceContextLoader,
)
from curvature_console.infrastructure.handoff import (
    HandoffStatus,
    create_handoff,
)
from curvature_console.infrastructure.handoff_proposal import (
    parse_handoff_proposals,
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
from curvature_console.presentation.handoff_controls_dialog import (
    HandoffControlsDialog,
    HandoffDeliveryProgressDialog,
    confirm_handoff_delivery,
    confirm_handoff_return,
)
from curvature_console.presentation.package_review_dialog import (
    PackageReviewDialog,
)
from curvature_console.presentation.reply_viewer_dialog import (
    ReplyViewerDialog,
)


@dataclass(frozen=True, slots=True)
class PendingBrowserExchange:
    """UI state belonging to exactly one immutable browser request."""

    request_id: str
    department_id: str
    user_task: str
    handoff_id: str | None = None
    handoff_return: bool = False
    handoff_update: bool = False


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
            repository_id: root.expanduser().resolve()
            for repository_id, root in (
                repository_roots
                if repository_roots is not None
                else {
                    "curvature-console": Path.cwd(),
                    "Curvature": Path("/home/seb/Curvature"),
                }
            ).items()
        }
        self.package_reviewer = PackageReviewer()
        self.package_applier = PackageApplier(
            reviewer=self.package_reviewer,
            backup_root=self.data_directory / "package-backups",
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
        self._handoff_progress_dialog: (
            HandoffDeliveryProgressDialog | None
        ) = None
        self._handoff_progress_request_id: str | None = None
        self._handoff_controls_dialog: HandoffControlsDialog | None = None

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
            panel.replies_view_requested.connect(self.show_reply_viewer)
            panel.workspace_state_changed.connect(self.save_department_state)
            panel.package_review_requested.connect(
                self.review_generated_package
            )
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

        self.handoff_controls_button = QPushButton("Bridge Controls")
        self.handoff_controls_button.setObjectName(
            "handoffBridgeControlsButton"
        )
        self.handoff_controls_button.setToolTip(
            "Review department-generated handoff drafts and supervise "
            "explicit interdepartmental delivery."
        )
        self.handoff_controls_button.clicked.connect(
            self.open_handoff_controls
        )

        toolbar = QToolBar("Workspace")
        toolbar.setObjectName("workspaceToolbar")
        toolbar.setMovable(False)
        toolbar.addWidget(self.restore_button)
        toolbar.addWidget(self.refresh_all_button)
        toolbar.addWidget(self.handoff_controls_button)
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

    def open_handoff_controls(self) -> None:
        """Open the supervised interdepartmental communication hub."""

        dialog = HandoffControlsDialog(
            state_store=self.state_store,
            parent=self,
        )
        self._handoff_controls_dialog = dialog
        dialog.deliver_requested.connect(self.deliver_handoff)
        dialog.return_requested.connect(self.return_handoff)
        dialog.update_requested.connect(self.update_handoff)
        try:
            dialog.exec()
        finally:
            self._handoff_controls_dialog = None

    def _refresh_handoff_controls(
        self,
        handoff_id: str | None = None,
    ) -> None:
        """Refresh the open Hub without losing the current handoff selection."""

        dialog = self._handoff_controls_dialog
        if dialog is not None and dialog.isVisible():
            dialog.reload(handoff_id)

    def deliver_handoff(self, handoff_id: str) -> None:
        """Deliver one approved handoff to its persisted target route."""

        if self._browser_worker is not None:
            QMessageBox.information(
                self,
                "ChatGPT operation in progress",
                "Wait for the current ChatGPT exchange before delivery.",
            )
            return

        record = self.state_store.load_handoff(handoff_id)
        if record is None:
            QMessageBox.critical(
                self,
                "Handoff unavailable",
                f"Unknown handoff: {handoff_id}",
            )
            return
        if record.status is not HandoffStatus.APPROVED:
            QMessageBox.warning(
                self,
                "Handoff not approved",
                "Only an approved handoff may be delivered.",
            )
            return

        route = self.state_store.load_chat_route(
            record.target_department_id
        )
        if route is None:
            QMessageBox.critical(
                self,
                "Target route unavailable",
                "The target department has no active conversation route.",
            )
            return

        if not confirm_handoff_delivery(
            parent=self,
            target_department_id=record.target_department_id,
            handoff_message=record.user_visible_message,
        ):
            return

        message_text = (
            f"CURVATURE_HANDOFF_ID: {record.handoff_id}\n"
            f"CURVATURE_REQUEST_ID: {record.request_id}\n\n"
            "# SUPERVISED INTERDEPARTMENTAL HANDOFF\n\n"
            f"Source department: {record.source_department_id}\n"
            f"Target department: {record.target_department_id}\n\n"
            f"{record.user_visible_message}\n\n"
            "Respond within the target department's authority. "
            "Do not silently perform another department's work."
        )
        sent = record.transition(HandoffStatus.SENT).append_message(
            record.source_department_id,
            "Controlled delivery started to "
            f"{record.target_department_id}.",
        )
        self.state_store.save_handoff(sent)
        self._refresh_handoff_controls(sent.handoff_id)

        request_id = f"handoff-{uuid4().hex}"
        self._pending_exchanges[request_id] = PendingBrowserExchange(
            request_id=request_id,
            department_id=record.target_department_id,
            user_task=message_text,
            handoff_id=record.handoff_id,
        )
        self._set_browser_operation_busy(
            True,
            record.target_department_id,
        )
        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id,
                department_id=record.target_department_id,
                message_text=message_text,
                create_new_thread=False,
                conversation_url=route.active_conversation_url,
                confirmation_marker=(
                    f"CURVATURE_HANDOFF_ID: {record.handoff_id}"
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
        self._show_handoff_progress(
            request_id=request_id,
            target_department_id=record.target_department_id,
            handoff_message=record.user_visible_message,
        )
        self.statusBar().showMessage(
            "Controlled handoff delivery engaged..."
        )
        worker.start()

    def update_handoff(self, handoff_id: str, update_text: str) -> None:
        """Send one supervised progress update within an open handoff."""

        if self._browser_worker is not None:
            QMessageBox.information(
                self,
                "ChatGPT operation in progress",
                "Wait for the current ChatGPT exchange before sending "
                "another progress update.",
            )
            return

        record = self.state_store.load_handoff(handoff_id)
        if record is None:
            QMessageBox.critical(
                self, "Handoff unavailable", f"Unknown handoff: {handoff_id}"
            )
            return
        if record.status is not HandoffStatus.IN_PROGRESS:
            QMessageBox.warning(
                self,
                "Handoff not in progress",
                "Only an in-progress handoff may receive a progress update.",
            )
            return
        clean_update = update_text.strip()
        if not clean_update:
            QMessageBox.warning(
                self,
                "Progress update required",
                "Enter the progress update before sending it.",
            )
            return

        route = self.state_store.load_chat_route(record.target_department_id)
        if route is None:
            QMessageBox.critical(
                self,
                "Target route unavailable",
                "The target department has no active conversation route.",
            )
            return

        message_text = (
            f"CURVATURE_HANDOFF_ID: {record.handoff_id}\n"
            f"CURVATURE_REQUEST_ID: {record.request_id}\n\n"
            "# SUPERVISED SAME-HANDOFF PROGRESS UPDATE\n\n"
            f"Source department: {record.source_department_id}\n"
            f"Target department: {record.target_department_id}\n\n"
            "The operator approved this update for the existing open "
            "handoff. Preserve the same handoff context and respond only "
            "within the target department's authority.\n\n"
            f"{clean_update}\n\n"
            "Return a progress response, blocker, decision request, milestone "
            "result or final result. Do not create an autonomous loop."
        )
        updating = record.transition(
            HandoffStatus.UPDATE_SENT
        ).append_message(
            record.source_department_id,
            "Operator-approved progress update sent to "
            + record.target_department_id
            + ":\n"
            + clean_update,
        )
        self.state_store.save_handoff(updating)
        self._refresh_handoff_controls(updating.handoff_id)

        request_id = f"handoff-update-{uuid4().hex}"
        self._pending_exchanges[request_id] = PendingBrowserExchange(
            request_id=request_id,
            department_id=record.target_department_id,
            user_task=message_text,
            handoff_id=record.handoff_id,
            handoff_update=True,
        )
        self._set_browser_operation_busy(True, record.target_department_id)
        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id,
                department_id=record.target_department_id,
                message_text=message_text,
                create_new_thread=False,
                conversation_url=route.active_conversation_url,
                confirmation_marker=(
                    f"CURVATURE_HANDOFF_ID: {record.handoff_id}"
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
        self._show_handoff_progress(
            request_id=request_id,
            target_department_id=record.target_department_id,
            handoff_message=clean_update,
        )
        self.statusBar().showMessage(
            "Supervised same-handoff update engaged..."
        )
        worker.start()

    def return_handoff(self, handoff_id: str) -> None:
        """Return the latest captured target reply once to the source route."""

        if self._browser_worker is not None:
            QMessageBox.information(
                self,
                "ChatGPT operation in progress",
                "Wait for the current ChatGPT exchange before returning a reply.",
            )
            return

        record = self.state_store.load_handoff(handoff_id)
        if record is None:
            QMessageBox.critical(
                self, "Handoff unavailable", f"Unknown handoff: {handoff_id}"
            )
            return
        if record.status not in {
            HandoffStatus.AWAITING_USER_DECISION,
            HandoffStatus.ANSWERED,
        }:
            QMessageBox.warning(
                self,
                "Reply not awaiting decision",
                "Only a captured target reply awaiting decision may be returned.",
            )
            return

        reply = next(
            (
                message.body
                for message in reversed(record.timeline)
                if message.author_department_id == record.target_department_id
                and not message.body.startswith("Delivery received by target")
            ),
            "",
        )
        if not reply:
            QMessageBox.critical(
                self,
                "Captured reply unavailable",
                "No target reply is available for this handoff.",
            )
            return

        route = self.state_store.load_chat_route(record.source_department_id)
        if route is None:
            QMessageBox.critical(
                self,
                "Source route unavailable",
                "The source department has no active conversation route.",
            )
            return

        if not confirm_handoff_return(
            parent=self,
            source_department_id=record.source_department_id,
            reply_text=reply,
        ):
            return

        message_text = (
            f"CURVATURE_HANDOFF_ID: {record.handoff_id}\n"
            f"CURVATURE_REQUEST_ID: {record.request_id}\n\n"
            "# SUPERVISED HANDOFF RETURN\n\n"
            f"Original source department: {record.source_department_id}\n"
            f"Target department: {record.target_department_id}\n\n"
            "The operator approved the following captured target reply "
            "for return to the original source department:\n\n"
            f"{reply}\n\n"
            "Review this update within the source department's authority. "
            "Do not automatically close the handoff or start another "
            "cross-department delivery."
        )
        returning = record.transition(HandoffStatus.RETURN_SENT).append_message(
            record.target_department_id,
            "Controlled return started to " + record.source_department_id + ".",
        )
        self.state_store.save_handoff(returning)
        self._refresh_handoff_controls(returning.handoff_id)

        request_id = f"handoff-return-{uuid4().hex}"
        self._pending_exchanges[request_id] = PendingBrowserExchange(
            request_id=request_id,
            department_id=record.source_department_id,
            user_task=message_text,
            handoff_id=record.handoff_id,
            handoff_return=True,
        )
        self._set_browser_operation_busy(True, record.source_department_id)
        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id,
                department_id=record.source_department_id,
                message_text=message_text,
                create_new_thread=False,
                conversation_url=route.active_conversation_url,
                confirmation_marker=(
                    f"CURVATURE_HANDOFF_ID: {record.handoff_id}"
                ),
            ),
        )
        worker.succeeded.connect(self._handle_browser_success)
        worker.failed.connect(self._handle_browser_failure)
        worker.route_unverified.connect(self._handle_browser_route_unverified)
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self._browser_worker = worker
        self._show_handoff_progress(
            request_id=request_id,
            target_department_id=record.source_department_id,
            handoff_message="# Return captured reply to source",
        )
        self.statusBar().showMessage("Controlled handoff return engaged...")
        worker.start()

    def _capture_department_handoff_proposals(
        self,
        pending: PendingBrowserExchange,
        response_text: str,
    ) -> tuple[int, tuple[str, ...]]:
        """Persist department-generated proposals as supervised draft handoffs."""

        parsed = parse_handoff_proposals(
            response_text,
            source_department_id=pending.department_id,
        )
        existing_ids = {
            record.handoff_id for record in self.state_store.load_handoffs()
        }
        captured = 0

        for index, proposal in enumerate(parsed.proposals):
            identity = "|".join(
                (
                    pending.request_id,
                    str(index),
                    pending.department_id,
                    proposal.target_department_id,
                    proposal.title,
                    proposal.task,
                )
            )
            handoff_id = (
                "handoff-proposal-"
                + sha256(identity.encode("utf-8")).hexdigest()[:24]
            )
            if handoff_id in existing_ids:
                continue

            record = create_handoff(
                handoff_id=handoff_id,
                request_id=f"proposal-{pending.request_id}-{index + 1}",
                source_department_id=pending.department_id,
                target_department_id=proposal.target_department_id,
                user_visible_message=proposal.render_visible_message(),
            )
            record = record.transition(
                HandoffStatus.PENDING_APPROVAL
            ).append_message(
                pending.department_id,
                "Department-generated proposal captured and queued for "
                "operator approval: "
                + proposal.title,
            )
            self.state_store.save_handoff(record)
            existing_ids.add(handoff_id)
            captured += 1

        return captured, parsed.errors

    def _record_handoff_answer(
        self,
        pending: PendingBrowserExchange,
        response_text: str,
    ) -> None:
        if pending.handoff_id is None:
            return
        record = self.state_store.load_handoff(pending.handoff_id)
        if record is None:
            return
        if pending.handoff_return:
            if record.status is HandoffStatus.RETURN_SENT:
                record = record.transition(
                    HandoffStatus.RETURNED
                ).append_message(
                    record.source_department_id,
                    "Returned update received by source conversation.",
                ).append_message(
                    record.source_department_id,
                    response_text,
                )
            self.state_store.save_handoff(record)
            self._refresh_handoff_controls(record.handoff_id)
            return

        if pending.handoff_update:
            if record.status is HandoffStatus.UPDATE_SENT:
                record = record.transition(
                    HandoffStatus.AWAITING_USER_DECISION
                ).append_message(
                    record.target_department_id,
                    response_text,
                )
            self.state_store.save_handoff(record)
            self._refresh_handoff_controls(record.handoff_id)
            return

        if record.status is HandoffStatus.SENT:
            record = record.transition(
                HandoffStatus.RECEIVED
            ).append_message(
                record.target_department_id,
                "Delivery received by target conversation.",
            )
        if record.status is HandoffStatus.RECEIVED:
            record = record.transition(
                HandoffStatus.AWAITING_USER_DECISION
            ).append_message(
                record.target_department_id,
                response_text,
            )
        self.state_store.save_handoff(record)
        self._refresh_handoff_controls(record.handoff_id)

    def _hold_failed_handoff(
        self,
        pending: PendingBrowserExchange,
        error_message: str,
    ) -> None:
        if pending.handoff_id is None:
            return
        record = self.state_store.load_handoff(pending.handoff_id)
        if record is None:
            return
        if pending.handoff_return:
            if record.status is not HandoffStatus.RETURN_SENT:
                return
            held = record.transition(HandoffStatus.HELD).append_message(
                record.target_department_id,
                "Controlled return failed and was held: " + error_message,
            )
        elif pending.handoff_update:
            if record.status is not HandoffStatus.UPDATE_SENT:
                return
            held = record.transition(HandoffStatus.HELD).append_message(
                record.source_department_id,
                "Progress update failed and was held: " + error_message,
            )
        else:
            if record.status is not HandoffStatus.SENT:
                return
            held = record.transition(HandoffStatus.HELD).append_message(
                record.source_department_id,
                "Controlled delivery failed and was held: " + error_message,
            )
        self.state_store.save_handoff(held)
        self._refresh_handoff_controls(held.handoff_id)

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
            f"Context refreshed: {loaded_total} documents · "
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

        if package.mode is TransferPackageMode.THREAD_HANDOFF:
            panel = self.department_panels[department_id]
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
        )
        self._pending_exchanges[request_id] = pending
        self._set_browser_operation_busy(True, department_id)
        self.statusBar().showMessage(
            f"Sending {package.mode.display_name} to "
            f"{panel.title_label.text()}..."
        )

        route = self.state_store.load_chat_route(department_id)
        confirmation_marker = (
            f"CURVATURE_REQUEST_ID: {request_id}"
        )
        message_text = (
            f"{confirmation_marker}\n\n{package.text}"
        )

        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id,
                department_id=department_id,
                message_text=message_text,
                create_new_thread=(
                    package.mode is TransferPackageMode.THREAD_HANDOFF
                ),
                conversation_url=(
                    route.active_conversation_url
                    if route is not None
                    else None
                ),
                confirmation_marker=confirmation_marker,
                attachment_paths=tuple(
                    record.path for record in panel.attachment_list.records
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
        downloaded_files: object,
    ) -> None:
        pending = self._pending_exchange(request_id, department_id)
        if pending is None:
            return

        self._finish_handoff_progress(request_id)
        self._pending_exchanges.pop(request_id, None)
        self._record_handoff_answer(pending, response_text)
        panel = self.department_panels[department_id]
        panel.append_browser_exchange(pending.user_task, response_text)
        captured_handoffs, handoff_errors = (
            self._capture_department_handoff_proposals(
                pending,
                response_text,
            )
        )

        captured_downloads = tuple(downloaded_files)
        self.state_store.save_generated_downloads(
            request_id=request_id,
            department_id=department_id,
            conversation_url=conversation_url,
            downloads=captured_downloads,
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
        download_count = len(captured_downloads)
        download_suffix = (
            f"; {download_count} generated file(s) captured"
            if download_count
            else ""
        )
        handoff_suffix = (
            f"; {captured_handoffs} handoff draft(s) awaiting review"
            if captured_handoffs
            else ""
        )
        error_suffix = (
            f"; {len(handoff_errors)} invalid handoff proposal(s) ignored"
            if handoff_errors
            else ""
        )
        self.statusBar().showMessage(
            f"ChatGPT response received and saved: "
            f"{panel.title_label.text()}{download_suffix}"
            f"{handoff_suffix}{error_suffix}"
        )

    def _handle_browser_route_unverified(
        self,
        request_id: str,
        department_id: str,
        observed_url: str,
        response_text: str,
    ) -> None:
        """Preserve only the response belonging to the current request."""

        pending = self._pending_exchange(request_id, department_id)
        if pending is None:
            return

        self._finish_handoff_progress(request_id)
        self._pending_exchanges.pop(request_id, None)
        self._record_handoff_answer(pending, response_text)
        panel = self.department_panels[department_id]
        panel.append_browser_exchange(pending.user_task, response_text)
        captured_handoffs, handoff_errors = (
            self._capture_department_handoff_proposals(
                pending,
                response_text,
            )
        )
        panel.input_editor.clear()
        self._set_browser_operation_busy(False, department_id)
        self.save_department_state(department_id)
        handoff_suffix = (
            f"; {captured_handoffs} handoff draft(s) awaiting review"
            if captured_handoffs
            else ""
        )
        error_suffix = (
            f"; {len(handoff_errors)} invalid handoff proposal(s) ignored"
            if handoff_errors
            else ""
        )
        self.statusBar().showMessage(
            f"ChatGPT response saved; route requires verification: "
            f"{panel.title_label.text()}{handoff_suffix}{error_suffix}"
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

        self._finish_handoff_progress(request_id)
        self._pending_exchanges.pop(request_id, None)
        self._hold_failed_handoff(pending, error_message)
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
        if self._handoff_progress_request_id == request_id:
            dialog = self._handoff_progress_dialog
            if dialog is not None:
                dialog.set_stage(stage)
        self.statusBar().showMessage(
            f"{panel.title_label.text()}: {stage}"
        )

    def _show_handoff_progress(
        self,
        *,
        request_id: str,
        target_department_id: str,
        handoff_message: str,
    ) -> None:
        first_line = handoff_message.splitlines()[0] if handoff_message else ""
        title = first_line.lstrip("# ").strip() or "Approved handoff"
        dialog = HandoffDeliveryProgressDialog(
            target_department_id=target_department_id,
            handoff_title=title,
            parent=self,
        )
        self._handoff_progress_request_id = request_id
        self._handoff_progress_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _finish_handoff_progress(self, request_id: str) -> None:
        if self._handoff_progress_request_id != request_id:
            return
        dialog = self._handoff_progress_dialog
        self._handoff_progress_request_id = None
        self._handoff_progress_dialog = None
        if dialog is not None:
            dialog.finish()
            dialog.deleteLater()

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
                conversation_text=panel.conversation_text(),
                draft_text=panel.input_editor.toPlainText(),
                attachments=panel.attachment_list.records,
            )
        )

    def review_generated_package(
        self,
        department_id: str,
        package_path_value: str,
    ) -> None:
        """Review a selected generated ZIP against its declared repository."""

        if department_id not in self.department_panels:
            raise ValueError(f"Unknown department: {department_id}")

        package_path = Path(package_path_value).expanduser().resolve()
        try:
            repository_id = self.package_reviewer.manifest_target_repository(
                package_path
            )
            repository_root = self.repository_roots.get(repository_id)
            if repository_root is None:
                raise PackageReviewError(
                    "No approved local repository is registered for package "
                    f"target: {repository_id}"
                )

            review = self.package_reviewer.review(
                package_path,
                repository_id=repository_id,
                repository_root=repository_root,
            )
        except (PackageReviewError, OSError) as exc:
            QMessageBox.critical(
                self,
                "Package review failed",
                str(exc),
            )
            return

        dialog = PackageReviewDialog(
            review,
            apply_callback=self.package_applier.apply,
            parent=self,
        )
        dialog.exec()

    def restore_persisted_state(self) -> None:
        """Restore department content, attachments and layout."""

        for department_id, panel in self.department_panels.items():
            state = self.state_store.load_department_state(department_id)
            if state is not None:
                panel.restore_conversation_text(state.conversation_text)
                panel.restore_reply_read_state(state.last_read_reply_count)
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
            conversation_text=panel.conversation_text(),
            draft_text=panel.input_editor.toPlainText(),
            last_read_reply_count=panel.last_read_reply_count,
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

    def show_reply_viewer(self, department_id: str) -> None:
        if department_id not in self.department_panels:
            raise ValueError(f"Unknown department: {department_id}")
        panel = self.department_panels[department_id]
        panel.mark_replies_read()
        self.save_department_state(department_id)
        ReplyViewerDialog(
            department_title=panel.title_label.text(),
            transcript=panel.conversation_text(),
            parent=self,
        ).exec()

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
