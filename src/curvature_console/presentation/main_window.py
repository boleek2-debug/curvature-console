"""Main three-panel desktop window for Curvature Console."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QLabel,
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
    CapturedDownload,
)
from curvature_console.infrastructure.package_apply import PackageApplier
from curvature_console.infrastructure.package_review import (
    PackageReviewError,
    PackageReviewer,
)
from curvature_console.infrastructure.console_request import (
    ArtifactTransportName,
    ConsoleRequest,
    build_artifact_transport_names,
    parse_console_requests,
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
from curvature_console.presentation.operational_conversations_dialog import (
    OperationalConversationsDialog,
)
from curvature_console.presentation.reply_viewer_dialog import (
    ReplyViewerDialog,
)
from curvature_console.presentation.support_unit_dialog import (
    ConsoleDevelopmentUnitDialog,
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
    support_unit: bool = False
    automatic_console_request: bool = False
    source_department_id: str | None = None
    source_request_id: str | None = None
    escalation_chain_id: str | None = None
    escalation_attempt: int = 0
    automatic_console_return: bool = False
    operational_conversation_id: str | None = None
    operational_operator_followup: bool = False
    artifact_transport_names: tuple[ArtifactTransportName, ...] = ()


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
        self._browser_queue: deque[BrowserBridgeWorker] = deque()
        self._pending_exchanges: dict[str, PendingBrowserExchange] = {}
        self._handoff_progress_dialog: (
            HandoffDeliveryProgressDialog | None
        ) = None
        self._handoff_progress_request_id: str | None = None
        self._handoff_progress_specs: dict[str, tuple[str, str]] = {}
        self._handoff_controls_dialog: HandoffControlsDialog | None = None
        self._support_unit_dialog: ConsoleDevelopmentUnitDialog | None = None
        self._operational_conversations_dialog: (
            OperationalConversationsDialog | None
        ) = None

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
            panel.abort_requested.connect(self.abort_browser_operation)
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

        self.support_unit_button = QPushButton("Console Development Unit")
        self.support_unit_button.setObjectName("supportUnitButton")
        self.support_unit_button.setToolTip(
            "Develop and diagnose Curvature Console, review repository state, "
            "logs and generated artifacts."
        )
        self.support_unit_button.clicked.connect(self.open_support_unit)

        toolbar = QToolBar("Workspace")
        toolbar.setObjectName("workspaceToolbar")
        toolbar.setMovable(False)
        toolbar.addWidget(self.restore_button)
        toolbar.addWidget(self.refresh_all_button)
        toolbar.addWidget(self.handoff_controls_button)
        toolbar.addWidget(self.support_unit_button)
        self.operational_conversations_button = QPushButton(
            "Operational Conversations"
        )
        self.operational_conversations_button.setObjectName(
            "operationalConversationsButton"
        )
        self.operational_conversations_button.clicked.connect(
            self.open_operational_conversations
        )
        toolbar.addWidget(self.operational_conversations_button)
        self.browser_queue_label = QLabel("Bridge queue: idle")
        self.browser_queue_label.setObjectName("browserBridgeQueueLabel")
        toolbar.addWidget(self.browser_queue_label)
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
        self._refresh_operational_review_button()
        self._restoring_state = False

    def open_operational_conversations(self) -> None:
        """Open the durable background conversation review surface."""

        dialog = OperationalConversationsDialog(
            state_store=self.state_store, parent=self
        )
        dialog.review_action_requested.connect(
            self._handle_operational_review_action
        )
        self._operational_conversations_dialog = dialog
        try:
            dialog.exec()
        finally:
            self._operational_conversations_dialog = None
            self._refresh_operational_review_button()

    def _refresh_operational_review_button(self) -> None:
        count = self.state_store.count_operational_reviews()
        label = "Operational Conversations"
        if count:
            label += f" ({count})"
        self.operational_conversations_button.setText(label)

    def _refresh_open_operational_dialog(self) -> None:
        dialog = self._operational_conversations_dialog
        if dialog is not None:
            dialog.refresh()
        self._refresh_operational_review_button()


    def _handle_operational_review_action(
        self, conversation_id: str, action: str, comment: str
    ) -> None:
        """Persist an operator decision and continue only when requested."""

        record = self.state_store.load_operational_conversation(conversation_id)
        if record is None:
            self.statusBar().showMessage("Operational conversation no longer exists.")
            return
        action = action.upper().strip()
        if action not in {"ACCEPT", "REJECT", "ASK"}:
            self.statusBar().showMessage("Unsupported operator review action.")
            return
        clean_comment = comment.strip()
        if action in {"REJECT", "ASK"} and not clean_comment:
            self.statusBar().showMessage(
                "Reject and Ask / Continue require an operator comment."
            )
            return

        labels = {
            "ACCEPT": "Accepted by operator",
            "REJECT": "Rejected by operator",
            "ASK": "Operator asked for continuation",
        }
        body = labels[action]
        if clean_comment:
            body += f"\n\n{clean_comment}"
        self.state_store.append_operational_message(
            conversation_id=conversation_id,
            author_department_id="operator",
            body=body,
        )

        if action == "ACCEPT":
            self.state_store.update_operational_conversation_status(
                conversation_id, "ACCEPTED"
            )
            self._refresh_open_operational_dialog()
            self.statusBar().showMessage(
                f"Operational result accepted: {record.title}"
            )
            return

        source_department_id = next(
            (
                participant
                for participant in record.participants
                if participant != "console-development"
            ),
            None,
        )
        if source_department_id is None:
            self.state_store.update_operational_conversation_status(
                conversation_id, "BLOCKED"
            )
            self._refresh_open_operational_dialog()
            self.statusBar().showMessage(
                "Operator feedback saved, but no source department route exists."
            )
            return
        route = self.state_store.load_chat_route(source_department_id)
        if route is None:
            self.state_store.update_operational_conversation_status(
                conversation_id, "BLOCKED"
            )
            self._refresh_open_operational_dialog()
            self.statusBar().showMessage(
                "Operator feedback saved, but the source department route "
                "is unavailable."
            )
            return

        request_id = f"operator-review-{uuid4().hex}"
        instruction = (
            f"CURVATURE_REQUEST_ID: {request_id}\n"
            f"SOURCE_REQUEST_ID: {record.source_request_id}\n"
            f"OPERATIONAL_CONVERSATION_ID: {conversation_id}\n"
            f"OPERATOR_REVIEW_ACTION: {action}\n\n"
            "# OPERATOR REVIEW CONTINUATION\n\n"
            f"The operator has {labels[action].lower()} for the existing "
            "operational conversation. Continue within the same source task and "
            "department authority. Do not create a new unrelated handoff.\n\n"
            f"## Operator comment\n{clean_comment}"
        )
        pending = PendingBrowserExchange(
            request_id=request_id,
            department_id=source_department_id,
            user_task=instruction,
            source_request_id=record.source_request_id,
            operational_conversation_id=conversation_id,
            operational_operator_followup=True,
        )
        self._pending_exchanges[request_id] = pending
        self.state_store.update_operational_conversation_status(
            conversation_id, "RUNNING"
        )
        self._set_browser_operation_busy(True, source_department_id)
        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id,
                department_id=source_department_id,
                message_text=instruction,
                create_new_thread=False,
                conversation_url=route.active_conversation_url,
                confirmation_marker=f"CURVATURE_REQUEST_ID: {request_id}",
            ),
        )
        worker.succeeded.connect(self._handle_browser_success)
        worker.failed.connect(self._handle_browser_failure)
        worker.cancelled.connect(self._handle_browser_cancelled)
        worker.route_unverified.connect(self._handle_browser_route_unverified)
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self._refresh_open_operational_dialog()
        self.statusBar().showMessage(
            f"Operator {action.lower()} queued for {source_department_id}"
        )
        self._enqueue_browser_worker(worker)

    def open_support_unit(self) -> None:
        """Open the Console Development Unit workspace and dedicated chat."""

        persisted = (
            self.state_store.load_department_state("console-development")
            or self.state_store.load_department_state("support")
        )
        dialog = ConsoleDevelopmentUnitDialog(
            repository_roots=self.repository_roots,
            data_directory=self.data_directory,
            conversation_text=(persisted.conversation_text if persisted else ""),
            draft_text=(persisted.draft_text if persisted else ""),
            attachment_records=(
                self.state_store.load_attachments("console-development")
                or self.state_store.load_attachments("support")
            ),
            download_records=(
                self.state_store.load_generated_downloads("console-development")
                or self.state_store.load_generated_downloads("support")
            ),
            parent=self,
        )
        self._support_unit_dialog = dialog
        dialog.send_requested.connect(self.start_support_exchange)
        try:
            dialog.exec()
        finally:
            self.state_store.save_department_state(
                "console-development", dialog.conversation_text(), dialog.draft_text()
            )
            self.state_store.replace_attachments(
                "console-development", dialog.attachment_records()
            )
            self._support_unit_dialog = None

    def start_support_exchange(
        self,
        message_text: str,
        attachment_paths: object,
        request_type: str = "CONSOLE_TOOL_REQUEST",
        requesting_department: str = "operator",
    ) -> None:
        """Send one operator-approved message to Console Development Unit."""

        dialog = self._support_unit_dialog
        if dialog is None:
            return
        request_id = f"console-dev-{uuid4().hex}"
        console_dev_case_id = f"console-dev-case-{uuid4().hex[:16]}"
        allowed_request_types = {
            "CONSOLE_TOOL_REQUEST",
            "CONSOLE_INTEGRATION_REQUEST",
            "CONSOLE_WORKFLOW_REQUEST",
            "CONSOLE_DEFECT",
            "CONSOLE_DECISION_REQUEST",
        }
        if request_type not in allowed_request_types:
            request_type = "CONSOLE_TOOL_REQUEST"
        allowed_departments = {
            "operator", "project", "core", "research", "console-development"
        }
        if requesting_department not in allowed_departments:
            requesting_department = "operator"

        payload = (
            f"CURVATURE_REQUEST_ID: {request_id}\n"
            f"CONSOLE_DEV_CASE_ID: {console_dev_case_id}\n"
            f"CONSOLE_REQUEST_TYPE: {request_type}\n"
            f"REQUESTING_DEPARTMENT: {requesting_department}\n\n"
            "# CURVATURE CONSOLE DEVELOPMENT UNIT REQUEST\n\n"
            "Act as the Curvature Console Development Unit. Own development, "
            "integration, diagnostics, workflows and validation for Curvature "
            "Console. Do not decide Chronicle product direction, gameplay, art "
            "direction or research conclusions. Diagnose accurately, do not "
            "invent missing state, and preserve Project/Core/Research authority "
            "boundaries.\n\n"
            "Routing rule: scope and priority decisions belong to Project; "
            "Chronicle implementation belongs to Core; evidence and licensing "
            "questions belong to Research; Console architecture, integrations "
            "and workflows belong to CDU. Identify a required handoff instead of "
            "silently performing another department's work.\n\n"
            f"Formal request type: {request_type}\n"
            f"Requesting department: {requesting_department}\n\n"
            f"Request body:\n{message_text.strip()}"
        )
        route = (
            self.state_store.load_chat_route("console-development")
            or self.state_store.load_chat_route("support")
        )
        pending = PendingBrowserExchange(
            request_id=request_id, department_id="console-development",
            user_task=message_text.strip(), support_unit=True
        )
        self._pending_exchanges[request_id] = pending
        dialog.set_busy(True, "Preparing request")
        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id, department_id="console-development",
                message_text=payload, create_new_thread=route is None,
                conversation_url=(route.active_conversation_url if route else None),
                confirmation_marker=f"CURVATURE_REQUEST_ID: {request_id}",
                attachment_paths=tuple(Path(path) for path in attachment_paths),
            ),
        )
        worker.succeeded.connect(self._handle_browser_success)
        worker.failed.connect(self._handle_browser_failure)
        worker.cancelled.connect(self._handle_browser_cancelled)
        worker.route_unverified.connect(self._handle_browser_route_unverified)
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self.statusBar().showMessage("Queueing request to Curvature Console Development Unit...")
        self._enqueue_browser_worker(worker)

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
        worker.cancelled.connect(self._handle_browser_cancelled)
        worker.route_unverified.connect(
            self._handle_browser_route_unverified
        )
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self._handoff_progress_specs[request_id] = (
            record.target_department_id,
            record.user_visible_message,
        )
        self.statusBar().showMessage(
            "Controlled handoff delivery queued..."
        )
        self._enqueue_browser_worker(worker)

    def update_handoff(self, handoff_id: str, update_text: str) -> None:
        """Send one supervised progress update within an open handoff."""

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
        worker.cancelled.connect(self._handle_browser_cancelled)
        worker.route_unverified.connect(
            self._handle_browser_route_unverified
        )
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self._handoff_progress_specs[request_id] = (
            record.target_department_id,
            clean_update,
        )
        self.statusBar().showMessage(
            "Supervised same-handoff update queued..."
        )
        self._enqueue_browser_worker(worker)

    def return_handoff(self, handoff_id: str) -> None:
        """Return the latest captured target reply once to the source route."""

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
        worker.cancelled.connect(self._handle_browser_cancelled)
        worker.route_unverified.connect(self._handle_browser_route_unverified)
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self._handoff_progress_specs[request_id] = (
            record.source_department_id,
            "# Return captured reply to source",
        )
        self.statusBar().showMessage("Controlled handoff return queued...")
        self._enqueue_browser_worker(worker)


    def _queue_automatic_console_request(
        self,
        *,
        source_pending: PendingBrowserExchange,
        request: ConsoleRequest,
        request_index: int,
    ) -> None:
        """Route a department-declared missing capability directly to CDU."""

        request_id = f"console-auto-{uuid4().hex}"
        case_id = f"console-dev-case-{uuid4().hex[:16]}"
        chain_id = (
            source_pending.escalation_chain_id
            or f"console-chain-{uuid4().hex}"
        )
        attempt = source_pending.escalation_attempt + 1
        body = request.render_request_body()
        payload = (
            f"CURVATURE_REQUEST_ID: {request_id}\n"
            f"CONSOLE_DEV_CASE_ID: {case_id}\n"
            f"CONSOLE_REQUEST_TYPE: {request.request_type}\n"
            f"REQUESTING_DEPARTMENT: {source_pending.department_id}\n"
            f"SOURCE_REQUEST_ID: {source_pending.request_id}\n"
            f"ESCALATION_CHAIN_ID: {chain_id}\n"
            f"ESCALATION_ATTEMPT: {attempt}\n\n"
            "# AUTOMATIC CONSOLE DEVELOPMENT ESCALATION\n\n"
            "The source department detected that it lacks a Console tool, "
            "integration or workflow required to continue its current task. "
            "Assess and fulfil this request within CDU authority. Do not make "
            "Project, Chronicle implementation or Research decisions.\n\n"
            "Completion rule: implementation is not complete until relevant "
            "tests and Console documentation are updated. Report any operator "
            "approval required for repository writes, installation, cost, "
            "security-sensitive actions or scope changes.\n\n"
            f"{body}"
        )
        route = (
            self.state_store.load_chat_route("console-development")
            or self.state_store.load_chat_route("support")
        )
        conversation_id = (
            source_pending.operational_conversation_id or chain_id
        )
        existing_conversation = self.state_store.load_operational_conversation(
            conversation_id
        )
        if existing_conversation is None:
            self.state_store.create_operational_conversation(
                conversation_id=conversation_id,
                source_request_id=(
                    source_pending.source_request_id or source_pending.request_id
                ),
                title=request.title,
                participants=(
                    source_pending.department_id,
                    "console-development",
                ),
                status="RUNNING",
            )
            round_number = 1
        else:
            round_number = self.state_store.begin_operational_round(
                conversation_id, title=request.title
            )
            self.state_store.append_operational_message(
                conversation_id=conversation_id,
                author_department_id="system",
                body=(
                    f"Operational conversation round {round_number} started.\n"
                    f"Technical escalation chain: {chain_id}\n"
                    f"Request: {request.title}"
                ),
            )
        transport_names = build_artifact_transport_names(
            request,
            request_id=request_id,
            round_number=round_number,
        )
        if transport_names:
            transport_lines = "\n".join(
                f"- Logical filename: {item.logical_filename}\n"
                f"  Required transport filename: {item.transport_filename}"
                for item in transport_names
            )
            payload += (
                "\n\n## Mandatory fresh-artifact transport contract\n\n"
                "Generate a new physical file object for this exact response. "
                "Do not reuse, relink or reattach a file card from an earlier "
                "message, even when the logical filename is unchanged. Attach "
                "the file using the exact unique transport filename below. "
                "The Console will validate the transport filename and map it "
                "back to the stable logical filename after capture.\n\n"
                f"{transport_lines}\n\n"
                "In the response metadata, report both logical_filename and "
                "transport_filename."
            )
        self.state_store.append_operational_message(
            conversation_id=conversation_id,
            author_department_id=source_pending.department_id,
            body=body,
        )
        pending = PendingBrowserExchange(
            request_id=request_id,
            department_id="console-development",
            user_task=body,
            support_unit=True,
            automatic_console_request=True,
            source_department_id=source_pending.department_id,
            source_request_id=(
                source_pending.source_request_id or source_pending.request_id
            ),
            escalation_chain_id=chain_id,
            escalation_attempt=attempt,
            operational_conversation_id=conversation_id,
            artifact_transport_names=transport_names,
        )
        self._pending_exchanges[request_id] = pending
        attachment_paths: tuple[Path, ...] = ()
        if request.request_type == "CONSOLE_DEFECT":
            candidates: list[Path] = []
            for directory, pattern in (
                (self.data_directory / "snapshots", "*.zip"),
                (self.data_directory / "logs", "*.log"),
            ):
                matches = sorted(
                    directory.glob(pattern),
                    key=lambda path: path.stat().st_mtime,
                    reverse=True,
                ) if directory.exists() else []
                if matches:
                    candidates.append(matches[0])
            attachment_paths = tuple(candidates)
        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id,
                department_id="console-development",
                message_text=payload,
                create_new_thread=route is None,
                conversation_url=(
                    route.active_conversation_url if route else None
                ),
                confirmation_marker=f"CURVATURE_REQUEST_ID: {request_id}",
                attachment_paths=attachment_paths,
            ),
        )
        worker.succeeded.connect(self._handle_browser_success)
        worker.failed.connect(self._handle_browser_failure)
        worker.cancelled.connect(self._handle_browser_cancelled)
        worker.route_unverified.connect(
            self._handle_browser_route_unverified
        )
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self.statusBar().showMessage(
            f"Automatic {source_pending.department_id} → CDU request queued: "
            f"{request.title}"
        )
        self._enqueue_browser_worker(worker)

    def _capture_and_queue_console_requests(
        self,
        pending: PendingBrowserExchange,
        response_text: str,
    ) -> tuple[int, tuple[str, ...]]:
        """Capture machine-readable CDU requests and queue them automatically."""

        parsed = parse_console_requests(response_text)
        if (
            pending.automatic_console_return
            and pending.escalation_attempt >= 2
            and parsed.requests
        ):
            if pending.operational_conversation_id:
                self.state_store.update_operational_conversation_status(
                    pending.operational_conversation_id,
                    "AWAITING_OPERATOR_DECISION",
                )
                self._refresh_open_operational_dialog()
            self.statusBar().showMessage(
                "Automatic CDU escalation stopped after two attempts; "
                "operator action is required."
            )
            return 0, parsed.errors + (
                "Automatic escalation chain reached its two-attempt limit.",
            )
        for index, request in enumerate(parsed.requests, start=1):
            self._queue_automatic_console_request(
                source_pending=pending,
                request=request,
                request_index=index,
            )
        return len(parsed.requests), parsed.errors

    @staticmethod
    def _canonical_transport_filename(filename: str) -> str:
        """Ignore only browser-added collision suffixes during transport checks."""

        path = Path(filename)
        stem = path.stem
        for suffix in tuple(f"({index})" for index in range(1, 1000)):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        return f"{stem}{path.suffix}".casefold()

    @staticmethod
    def _collision_safe_artifact_path(directory: Path, filename: str) -> Path:
        """Return a non-destructive local path for one logical artifact version."""

        candidate = directory / Path(filename).name
        if not candidate.exists():
            return candidate
        path = Path(filename)
        index = 2
        while True:
            candidate = directory / f"{path.stem}-{index}{path.suffix}"
            if not candidate.exists():
                return candidate
            index += 1

    def _normalize_console_artifacts(
        self,
        *,
        pending: PendingBrowserExchange,
        downloaded_files: tuple[object, ...],
    ) -> tuple[tuple[object, ...], tuple[str, ...]]:
        """Validate fresh transport names and map them to stable logical names."""

        mappings = pending.artifact_transport_names
        if not mappings:
            return downloaded_files, ()

        expected = {
            self._canonical_transport_filename(item.transport_filename): item
            for item in mappings
        }
        matched: set[str] = set()
        normalized: list[CapturedDownload] = []
        errors: list[str] = []

        for download in downloaded_files:
            original_filename = str(getattr(download, "original_filename", ""))
            key = self._canonical_transport_filename(original_filename)
            mapping = expected.get(key)
            if mapping is None:
                errors.append(
                    "Rejected unexpected or stale CDU artifact: "
                    f"{original_filename or '<unnamed>'}."
                )
                continue
            saved_path = Path(getattr(download, "saved_path"))
            destination = self._collision_safe_artifact_path(
                saved_path.parent,
                mapping.logical_filename,
            )
            if saved_path != destination:
                saved_path.replace(destination)
            normalized.append(
                CapturedDownload(
                    original_filename=mapping.logical_filename,
                    saved_path=destination,
                    source_url=str(getattr(download, "source_url", "")),
                    size_bytes=destination.stat().st_size,
                )
            )
            matched.add(key)

        for key, mapping in expected.items():
            if key not in matched:
                errors.append(
                    "Missing required fresh CDU transport artifact: "
                    f"{mapping.transport_filename} "
                    f"(logical {mapping.logical_filename})."
                )

        return tuple(normalized), tuple(errors)

    def _queue_console_result_return(
        self,
        *,
        pending: PendingBrowserExchange,
        response_text: str,
        downloaded_files: tuple[object, ...],
    ) -> None:
        """Return CDU output to the originating department and resume its task."""

        source_department_id = pending.source_department_id
        if not source_department_id:
            return
        route = self.state_store.load_chat_route(source_department_id)
        if route is None:
            self.statusBar().showMessage(
                "CDU result captured, but source route is unavailable: "
                + source_department_id
            )
            return
        artifact_lines: list[str] = []
        for item in downloaded_files:
            path_value = getattr(item, "saved_path", None)
            path = Path(path_value) if path_value is not None else None
            logical_name = str(
                getattr(item, "original_filename", path.name if path else item)
            )
            if path is not None and path.is_file():
                data = path.read_bytes()
                artifact_lines.append(
                    f"- logical_filename={logical_name}; "
                    f"saved_path={path}; size_bytes={len(data)}; "
                    f"sha256={sha256(data).hexdigest()}"
                )
            else:
                artifact_lines.append(f"- logical_filename={logical_name}")
        artifacts = "\n".join(artifact_lines) or "- none"
        request_id = f"console-return-{uuid4().hex}"
        message_text = (
            f"CURVATURE_REQUEST_ID: {request_id}\n"
            f"SOURCE_REQUEST_ID: {pending.source_request_id or ''}\n"
            f"ESCALATION_CHAIN_ID: {pending.escalation_chain_id or ''}\n"
            f"ESCALATION_ATTEMPT: {pending.escalation_attempt}\n\n"
            "# AUTOMATIC CONSOLE DEVELOPMENT RESULT RETURN\n\n"
            "Console Development Unit completed or assessed the automatically "
            "escalated request. Continue the original task within your own "
            "department authority. Do not repeat the CDU work. If an operator "
            "approval is still required, state exactly what must be approved.\n\n"
            f"## CDU response\n{response_text}\n\n"
            f"## Captured artifacts\n{artifacts}"
        )
        source_pending = PendingBrowserExchange(
            request_id=request_id,
            department_id=source_department_id,
            user_task=message_text,
            source_request_id=pending.source_request_id,
            escalation_chain_id=pending.escalation_chain_id,
            escalation_attempt=pending.escalation_attempt,
            automatic_console_return=True,
            operational_conversation_id=pending.operational_conversation_id,
        )
        self._pending_exchanges[request_id] = source_pending
        self._set_browser_operation_busy(True, source_department_id)
        worker = BrowserBridgeWorker(
            config=self.browser_config,
            request=BrowserExchangeRequest(
                request_id=request_id,
                department_id=source_department_id,
                message_text=message_text,
                create_new_thread=False,
                conversation_url=route.active_conversation_url,
                confirmation_marker=f"CURVATURE_REQUEST_ID: {request_id}",
            ),
        )
        worker.succeeded.connect(self._handle_browser_success)
        worker.failed.connect(self._handle_browser_failure)
        worker.cancelled.connect(self._handle_browser_cancelled)
        worker.route_unverified.connect(
            self._handle_browser_route_unverified
        )
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self.statusBar().showMessage(
            f"CDU result queued for automatic return to {source_department_id}"
        )
        self._enqueue_browser_worker(worker)

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
        worker.cancelled.connect(self._handle_browser_cancelled)
        worker.route_unverified.connect(
            self._handle_browser_route_unverified
        )
        worker.stage_changed.connect(self._handle_browser_stage)
        worker.finished.connect(self._clear_browser_worker)
        self._enqueue_browser_worker(worker)

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
        if pending.support_unit:
            dialog = self._support_unit_dialog
            if dialog is not None:
                dialog.append_exchange(pending.user_task, response_text)
                dialog.set_busy(False)
                self.state_store.save_department_state(
                    "console-development", dialog.conversation_text(), dialog.draft_text()
                )
            self.state_store.save_chat_route(
                department_id="console-development", project_name=project_name,
                project_url=project_url, active_conversation_url=conversation_url
            )
            captured_console_downloads = tuple(downloaded_files)
            transport_errors: tuple[str, ...] = ()
            if pending.automatic_console_request:
                captured_console_downloads, transport_errors = (
                    self._normalize_console_artifacts(
                        pending=pending,
                        downloaded_files=captured_console_downloads,
                    )
                )
            self.state_store.save_generated_downloads(
                request_id=request_id, department_id="console-development",
                conversation_url=conversation_url,
                downloads=captured_console_downloads,
            )
            if dialog is not None:
                dialog.set_generated_downloads(
                    self.state_store.load_generated_downloads("console-development")
                )
                dialog.clear_sent_attachments()
                self.state_store.replace_attachments("console-development", ())
            self.statusBar().showMessage(
                "Console Development response received and saved"
                + (
                    f"; {len(transport_errors)} fresh-artifact validation error(s)"
                    if transport_errors else ""
                )
            )
            if pending.automatic_console_request:
                if pending.operational_conversation_id:
                    artifacts = tuple(
                        str(getattr(item, "saved_path", item))
                        for item in captured_console_downloads
                    )
                    artifact_text = (
                        "\n\nCaptured artifacts:\n"
                        + "\n".join(f"- {item}" for item in artifacts)
                        if artifacts
                        else ""
                    )
                    self.state_store.append_operational_message(
                        conversation_id=pending.operational_conversation_id,
                        author_department_id="console-development",
                        body=response_text + artifact_text,
                    )
                    if transport_errors:
                        self.state_store.append_operational_message(
                            conversation_id=pending.operational_conversation_id,
                            author_department_id="system",
                            body=(
                                "Fresh-artifact transport validation failed:\n- "
                                + "\n- ".join(transport_errors)
                            ),
                        )
                    self.state_store.update_operational_conversation_status(
                        pending.operational_conversation_id, "WAITING_SOURCE"
                    )
                    self._refresh_open_operational_dialog()
                return_response = response_text
                if transport_errors:
                    return_response += (
                        "\n\n## Console fresh-artifact validation\n"
                        "FAILED\n- " + "\n- ".join(transport_errors)
                    )
                elif pending.artifact_transport_names:
                    return_response += (
                        "\n\n## Console fresh-artifact validation\nPASS"
                    )
                self._queue_console_result_return(
                    pending=pending,
                    response_text=return_response,
                    downloaded_files=captured_console_downloads,
                )
            return
        panel = self.department_panels[department_id]
        panel.append_browser_exchange(pending.user_task, response_text)
        if (
            pending.operational_operator_followup
            and pending.operational_conversation_id
        ):
            self.state_store.append_operational_message(
                conversation_id=pending.operational_conversation_id,
                author_department_id=department_id,
                body=response_text,
            )
            parsed_followups = parse_console_requests(response_text)
            followup_status = (
                "RUNNING" if parsed_followups.requests else "RESULT_READY"
            )
            self.state_store.update_operational_conversation_status(
                pending.operational_conversation_id, followup_status
            )
            self._refresh_open_operational_dialog()
        captured_handoffs, handoff_errors = (
            self._capture_department_handoff_proposals(
                pending,
                response_text,
            )
        )
        captured_console_requests, console_request_errors = (
            self._capture_and_queue_console_requests(
                pending,
                response_text,
            )
        )
        if pending.automatic_console_return and pending.operational_conversation_id:
            self.state_store.append_operational_message(
                conversation_id=pending.operational_conversation_id,
                author_department_id=department_id,
                body=response_text,
            )
            final_status = (
                "RUNNING" if captured_console_requests else "RESULT_READY"
            )
            self.state_store.update_operational_conversation_status(
                pending.operational_conversation_id, final_status
            )
            self._refresh_open_operational_dialog()

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
        console_suffix = (
            f"; {captured_console_requests} automatic CDU request(s) queued"
            if captured_console_requests
            else ""
        )
        console_error_suffix = (
            f"; {len(console_request_errors)} invalid CDU request(s) ignored"
            if console_request_errors
            else ""
        )
        self.statusBar().showMessage(
            f"ChatGPT response received and saved: "
            f"{panel.title_label.text()}{download_suffix}"
            f"{handoff_suffix}{console_suffix}{error_suffix}"
            f"{console_error_suffix}"
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
        if pending.support_unit:
            dialog = self._support_unit_dialog
            if dialog is not None:
                dialog.append_exchange(pending.user_task, response_text)
                dialog.set_busy(False)
                self.state_store.save_department_state(
                    "console-development", dialog.conversation_text(), dialog.draft_text()
                )
            self.statusBar().showMessage(
                "Console Development response saved; conversation route requires verification"
            )
            QMessageBox.warning(
                self, "Console Development route requires verification",
                f"Response was captured, but the observed route was:\n{observed_url}"
            )
            return
        panel = self.department_panels[department_id]
        panel.append_browser_exchange(pending.user_task, response_text)
        if (
            pending.operational_operator_followup
            and pending.operational_conversation_id
        ):
            self.state_store.append_operational_message(
                conversation_id=pending.operational_conversation_id,
                author_department_id=department_id,
                body=response_text,
            )
            parsed_followups = parse_console_requests(response_text)
            followup_status = (
                "RUNNING" if parsed_followups.requests else "RESULT_READY"
            )
            self.state_store.update_operational_conversation_status(
                pending.operational_conversation_id, followup_status
            )
            self._refresh_open_operational_dialog()
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

    def _handle_browser_cancelled(
        self,
        request_id: str,
        department_id: str,
        submitted: bool,
    ) -> None:
        pending = self._pending_exchange(request_id, department_id)
        if pending is None:
            return

        self._finish_handoff_progress(request_id)
        self._pending_exchanges.pop(request_id, None)
        message = (
            "Browser request cancelled after submission."
            if submitted
            else "Browser request cancelled before submission."
        )
        self._hold_failed_handoff(pending, message)
        self._set_browser_operation_busy(False, department_id)
        if pending.support_unit:
            dialog = self._support_unit_dialog
            if dialog is not None:
                dialog.set_busy(False)
        self.statusBar().showMessage(message)

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
        if pending.support_unit:
            dialog = self._support_unit_dialog
            if dialog is not None:
                dialog.set_busy(False)
            self.statusBar().showMessage("Console Development browser operation failed")
            QMessageBox.critical(self, "ChatGPT browser bridge failed", error_message)
            return
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

        if pending := self._pending_exchange(request_id, department_id):
            if pending.support_unit:
                dialog = self._support_unit_dialog
                if dialog is not None:
                    dialog.set_stage(stage)
                self.statusBar().showMessage(f"Console Development: {stage}")
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
        self._handoff_progress_specs.pop(request_id, None)
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

        if active_department_id == "console-development":
            dialog = self._support_unit_dialog
            if dialog is not None:
                dialog.set_busy(busy)
            return
        panel = self.department_panels[active_department_id]
        panel.set_browser_busy(busy)

    def _enqueue_browser_worker(self, worker: BrowserBridgeWorker) -> None:
        """Queue one browser exchange and start it when the bridge is free."""

        self._browser_queue.append(worker)
        self._refresh_browser_queue_status()
        if self._browser_worker is None:
            self._start_next_browser_worker()

    def _start_next_browser_worker(self) -> None:
        if self._browser_worker is not None or not self._browser_queue:
            self._refresh_browser_queue_status()
            return
        worker = self._browser_queue.popleft()
        self._browser_worker = worker
        request = getattr(worker, "request", None)
        request_id = getattr(request, "request_id", "")
        spec = self._handoff_progress_specs.get(request_id)
        if spec is not None:
            self._show_handoff_progress(
                request_id=request_id,
                target_department_id=spec[0],
                handoff_message=spec[1],
            )
        self._refresh_browser_queue_status()
        worker.start()

    def abort_browser_operation(self, department_id: str) -> None:
        """Abort the active exchange or remove the oldest queued one for a department."""

        active = self._browser_worker
        active_request = getattr(active, "request", None)
        if active is not None and getattr(active_request, "department_id", None) == department_id:
            active.request_cancel()
            self.statusBar().showMessage(
                f"Cancelling active Browser Bridge request: {department_id}"
            )
            return

        for worker in tuple(self._browser_queue):
            request = getattr(worker, "request", None)
            if getattr(request, "department_id", None) != department_id:
                continue
            self._browser_queue.remove(worker)
            request_id = getattr(request, "request_id", "")
            pending = self._pending_exchanges.pop(request_id, None)
            self._handoff_progress_specs.pop(request_id, None)
            if pending is not None:
                self._hold_failed_handoff(pending, "Queued request cancelled by operator.")
            self._set_browser_operation_busy(False, department_id)
            worker.deleteLater()
            self._refresh_browser_queue_status()
            self.statusBar().showMessage(
                f"Cancelled queued Browser Bridge request: {department_id}"
            )
            return

    def _refresh_browser_queue_status(self) -> None:
        active = self._browser_worker
        waiting = len(self._browser_queue)
        if active is None:
            text = f"Bridge queue: {waiting} waiting" if waiting else "Bridge queue: idle"
        else:
            request = getattr(active, "request", None)
            department_id = getattr(request, "department_id", "unknown")
            text = f"Bridge active: {department_id} · {waiting} waiting"
        self.browser_queue_label.setText(text)

    def _clear_browser_worker(self) -> None:
        worker = self._browser_worker
        self._browser_worker = None
        if worker is not None:
            worker.deleteLater()
        self._start_next_browser_worker()

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

        if self._browser_worker is not None or self._browser_queue:
            QMessageBox.information(
                self,
                "ChatGPT operation in progress",
                "Wait for the active and queued ChatGPT exchanges before closing "
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
