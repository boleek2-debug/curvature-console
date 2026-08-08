"""Read-only operator work-state surface for Curvature Console."""

from __future__ import annotations

from collections import Counter

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.handoff import HandoffStatus
from curvature_console.infrastructure.state_store import SQLiteStateStore
from curvature_console.infrastructure.thread_pressure import (
    ThreadPressureEstimator,
    active_thread_conversation_text,
)


_ACTIVE_OPERATIONAL_STATUSES = frozenset({"RUNNING", "WAITING_SOURCE"})
_ATTENTION_OPERATIONAL_STATUSES = frozenset(
    {"RESULT_READY", "BLOCKED", "AWAITING_OPERATOR_DECISION"}
)
_ACTIVE_BROWSER_STATES = frozenset(
    {"QUEUED", "STARTED", "SUBMITTED", "RESPONSE_RECEIVED"}
)
_RECOVERY_BROWSER_STATES = frozenset({"RETRY_PENDING", "RECONCILE_REQUIRED"})
_ACTIVE_HANDOFF_STATUSES = frozenset(
    {
        HandoffStatus.APPROVED,
        HandoffStatus.SENT,
        HandoffStatus.RECEIVED,
        HandoffStatus.IN_PROGRESS,
        HandoffStatus.UPDATE_SENT,
        HandoffStatus.RETURN_SENT,
    }
)
_ATTENTION_HANDOFF_STATUSES = frozenset(
    {
        HandoffStatus.DRAFT,
        HandoffStatus.PENDING_APPROVAL,
        HandoffStatus.ANSWERED,
        HandoffStatus.AWAITING_USER_DECISION,
        HandoffStatus.RETURNED,
        HandoffStatus.HELD,
    }
)
_DEPARTMENTS = (
    ("project", "Project"),
    ("core", "Core"),
    ("research", "Research"),
)


class WorkStateSurface(QWidget):
    """Present cross-department state and first-class Project continuity controls."""

    open_department_requested = Signal(str)
    department_transfer_requested = Signal(str, str)
    research_add_sources_requested = Signal()

    def __init__(
        self,
        *,
        state_store: SQLiteStateStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state_store = state_store
        self.thread_pressure_estimator = ThreadPressureEstimator()
        self.setObjectName("workStateSurface")

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Work")
        title.setObjectName("workStateTitle")
        title.setProperty("heading", True)
        subtitle = QLabel(
            "Operational overview with direct Project continuity controls. "
            "Existing department workspaces remain available."
        )
        subtitle.setObjectName("workStateSubtitle")
        subtitle.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header.addLayout(title_block, 1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("workStateRefreshButton")
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        summary_frame = QFrame()
        summary_frame.setObjectName("workStateSummaryFrame")
        summary_layout = QGridLayout(summary_frame)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setHorizontalSpacing(12)
        summary_layout.setVerticalSpacing(8)

        self.attention_summary = self._summary_card("Needs attention", "0")
        self.active_summary = self._summary_card("Active work", "0")
        self.bridge_summary = self._summary_card("Bridge", "Idle")
        self.output_summary = self._summary_card("Generated files", "0")
        for column, card in enumerate(
            (
                self.attention_summary,
                self.active_summary,
                self.bridge_summary,
                self.output_summary,
            )
        ):
            summary_layout.addWidget(card, 0, column)
        root.addWidget(summary_frame)

        project_group = QGroupBox("Project — primary operator workspace")
        project_group.setObjectName("workStateProjectGroup")
        project_layout = QVBoxLayout(project_group)

        self.project_status_label = QLabel()
        self.project_status_label.setObjectName("workStateProjectStatus")
        self.project_status_label.setWordWrap(True)
        project_layout.addWidget(self.project_status_label)

        self.project_conversation_preview = QPlainTextEdit()
        self.project_conversation_preview.setObjectName(
            "workStateProjectConversationPreview"
        )
        self.project_conversation_preview.setReadOnly(True)
        self.project_conversation_preview.setMinimumHeight(150)
        self.project_conversation_preview.setPlaceholderText(
            "No persisted Project conversation yet."
        )
        project_layout.addWidget(self.project_conversation_preview, 1)

        project_layout.addWidget(QLabel("Current Project draft"))
        self.project_draft_preview = QPlainTextEdit()
        self.project_draft_preview.setObjectName("workStateProjectDraftPreview")
        self.project_draft_preview.setReadOnly(True)
        self.project_draft_preview.setMaximumHeight(90)
        self.project_draft_preview.setPlaceholderText("No current Project draft.")
        project_layout.addWidget(self.project_draft_preview)

        project_actions = QHBoxLayout()
        self.open_project_button = QPushButton("Open Project Workspace")
        self.open_project_button.setObjectName("workStateOpenProjectButton")
        self.open_project_button.clicked.connect(
            lambda: self.open_department_requested.emit("project")
        )
        project_actions.addWidget(self.open_project_button)

        self.project_task_button = QPushButton("Send Project Task")
        self.project_task_button.setObjectName("workStateProjectTaskButton")
        self.project_task_button.clicked.connect(
            lambda: self.department_transfer_requested.emit("project", "task")
        )
        project_actions.addWidget(self.project_task_button)

        self.project_handoff_button = QPushButton("Thread Handoff Package")
        self.project_handoff_button.setObjectName("workStateProjectHandoffButton")
        self.project_handoff_button.clicked.connect(
            lambda: self.department_transfer_requested.emit(
                "project", "thread_handoff"
            )
        )
        project_actions.addWidget(self.project_handoff_button)
        project_actions.addStretch(1)
        project_layout.addLayout(project_actions)
        root.addWidget(project_group, 2)

        department_workspaces = QGridLayout()
        department_workspaces.setHorizontalSpacing(12)
        department_workspaces.setVerticalSpacing(8)

        research_group = QGroupBox("Research — sources and evidence workspace")
        research_group.setObjectName("workStateResearchGroup")
        research_layout = QVBoxLayout(research_group)
        self.research_status_label = QLabel()
        self.research_status_label.setObjectName("workStateResearchStatus")
        self.research_status_label.setWordWrap(True)
        research_layout.addWidget(self.research_status_label)

        self.research_sources_list = QListWidget()
        self.research_sources_list.setObjectName("workStateResearchSourcesList")
        self.research_sources_list.setMaximumHeight(110)
        research_layout.addWidget(self.research_sources_list)

        research_actions = QHBoxLayout()
        self.open_research_button = QPushButton("Open Research Workspace")
        self.open_research_button.setObjectName("workStateOpenResearchButton")
        self.open_research_button.clicked.connect(
            lambda: self.open_department_requested.emit("research")
        )
        research_actions.addWidget(self.open_research_button)

        self.research_add_sources_button = QPushButton("Add Sources / Materials")
        self.research_add_sources_button.setObjectName(
            "workStateResearchAddSourcesButton"
        )
        self.research_add_sources_button.clicked.connect(
            self.research_add_sources_requested.emit
        )
        research_actions.addWidget(self.research_add_sources_button)

        self.research_task_button = QPushButton("Send Research Task")
        self.research_task_button.setObjectName("workStateResearchTaskButton")
        self.research_task_button.clicked.connect(
            lambda: self.department_transfer_requested.emit("research", "task")
        )
        research_actions.addWidget(self.research_task_button)

        self.research_handoff_button = QPushButton("Thread Handoff Package")
        self.research_handoff_button.setObjectName(
            "workStateResearchHandoffButton"
        )
        self.research_handoff_button.clicked.connect(
            lambda: self.department_transfer_requested.emit(
                "research", "thread_handoff"
            )
        )
        research_actions.addWidget(self.research_handoff_button)
        research_actions.addStretch(1)
        research_layout.addLayout(research_actions)

        core_group = QGroupBox("Core — implementation and output workspace")
        core_group.setObjectName("workStateCoreGroup")
        core_layout = QVBoxLayout(core_group)
        self.core_status_label = QLabel()
        self.core_status_label.setObjectName("workStateCoreStatus")
        self.core_status_label.setWordWrap(True)
        core_layout.addWidget(self.core_status_label)

        self.core_outputs_list = QListWidget()
        self.core_outputs_list.setObjectName("workStateCoreOutputsList")
        self.core_outputs_list.setMaximumHeight(110)
        core_layout.addWidget(self.core_outputs_list)

        core_actions = QHBoxLayout()
        self.open_core_button = QPushButton("Open Core Workspace")
        self.open_core_button.setObjectName("workStateOpenCoreButton")
        self.open_core_button.clicked.connect(
            lambda: self.open_department_requested.emit("core")
        )
        core_actions.addWidget(self.open_core_button)

        self.core_task_button = QPushButton("Send Core Task")
        self.core_task_button.setObjectName("workStateCoreTaskButton")
        self.core_task_button.clicked.connect(
            lambda: self.department_transfer_requested.emit("core", "task")
        )
        core_actions.addWidget(self.core_task_button)

        self.core_handoff_button = QPushButton("Thread Handoff Package")
        self.core_handoff_button.setObjectName("workStateCoreHandoffButton")
        self.core_handoff_button.clicked.connect(
            lambda: self.department_transfer_requested.emit(
                "core", "thread_handoff"
            )
        )
        core_actions.addWidget(self.core_handoff_button)
        core_actions.addStretch(1)
        core_layout.addLayout(core_actions)

        department_workspaces.addWidget(research_group, 0, 0)
        department_workspaces.addWidget(core_group, 0, 1)
        department_workspaces.setColumnStretch(0, 1)
        department_workspaces.setColumnStretch(1, 1)
        root.addLayout(department_workspaces)

        content = QGridLayout()
        content.setHorizontalSpacing(12)
        content.setVerticalSpacing(12)

        self.attention_list = QListWidget()
        self.attention_list.setObjectName("workStateAttentionList")
        self.active_list = QListWidget()
        self.active_list.setObjectName("workStateActiveList")
        self.department_list = QListWidget()
        self.department_list.setObjectName("workStateDepartmentList")
        self.result_list = QListWidget()
        self.result_list.setObjectName("workStateResultList")

        content.addWidget(
            self._group("Needs Attention", self.attention_list), 0, 0
        )
        content.addWidget(self._group("Active Work", self.active_list), 0, 1)
        content.addWidget(
            self._group("Departments", self.department_list), 1, 0
        )
        content.addWidget(
            self._group("Recent Results / Outputs", self.result_list), 1, 1
        )
        content.setColumnStretch(0, 1)
        content.setColumnStretch(1, 1)
        content.setRowStretch(0, 1)
        content.setRowStretch(1, 1)
        root.addLayout(content, 1)

        self.footer_label = QLabel(
            "B8C prototype: Project task and Thread Handoff controls reuse the "
            "existing supervised Browser Bridge workflow. Repository writes "
            "remain unchanged and operator-controlled."
        )
        self.footer_label.setObjectName("workStateFooter")
        self.footer_label.setWordWrap(True)
        root.addWidget(self.footer_label)

        self.refresh()

    @staticmethod
    def _summary_card(title: str, value: str) -> QGroupBox:
        card = QGroupBox(title)
        card.setObjectName("workStateSummaryCard")
        layout = QVBoxLayout(card)
        label = QLabel(value)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("workStateSummaryValue")
        layout.addWidget(label)
        return card

    @staticmethod
    def _group(title: str, widget: QWidget) -> QGroupBox:
        group = QGroupBox(title)
        group.setObjectName("workStateGroup")
        layout = QVBoxLayout(group)
        layout.addWidget(widget)
        return group

    @staticmethod
    def _set_card_value(card: QGroupBox, value: str) -> None:
        label = card.findChild(QLabel, "workStateSummaryValue")
        if label is not None:
            label.setText(value)

    @staticmethod
    def _populate_list(widget: QListWidget, rows: list[str], empty: str) -> None:
        widget.clear()
        if rows:
            widget.addItems(rows)
        else:
            widget.addItem(empty)

    def _department_workspace_snapshot(self, department_id: str):
        state = self.state_store.load_department_state(department_id)
        attachments = self.state_store.load_attachments(department_id)
        route = self.state_store.load_chat_route(department_id)

        conversation_text = state.conversation_text if state is not None else ""
        draft_text = state.draft_text if state is not None else ""
        pressure = self.thread_pressure_estimator.estimate(
            active_thread_conversation_text(conversation_text),
            draft_text,
            (record.path for record in attachments),
        )
        route_text = (
            "connected"
            if route is not None and route.active_conversation_url
            else "not set"
        )
        return (
            conversation_text,
            draft_text,
            attachments,
            pressure,
            route_text,
        )

    def _refresh_department_workspaces(self, downloads) -> None:
        (
            project_conversation,
            project_draft,
            project_attachments,
            project_pressure,
            project_route,
        ) = self._department_workspace_snapshot("project")
        self.project_status_label.setText(
            f"Thread pressure: {project_pressure.level.value} · "
            f"~{project_pressure.estimated_tokens:,} tokens · "
            f"Attachments: {len(project_attachments)} · "
            f"Route: {project_route}. "
            f"{project_pressure.handoff_recommendation}"
        )
        # Keep the operator surface readable: show the tail of the persisted
        # Project transcript while the full conversation remains in Project.
        transcript_tail = project_conversation[-12000:]
        self.project_conversation_preview.setPlainText(transcript_tail)
        self.project_draft_preview.setPlainText(project_draft)
        self.project_handoff_button.setText(
            "Thread Handoff Package (Recommended)"
            if project_pressure.should_prepare_handoff
            else "Thread Handoff Package"
        )

        (
            _research_conversation,
            research_draft,
            research_attachments,
            research_pressure,
            research_route,
        ) = self._department_workspace_snapshot("research")
        self.research_status_label.setText(
            f"Thread pressure: {research_pressure.level.value} · "
            f"~{research_pressure.estimated_tokens:,} tokens · "
            f"Sources/materials: {len(research_attachments)} · "
            f"Route: {research_route}. "
            f"{research_pressure.handoff_recommendation}"
        )
        research_rows = [
            record.path.name for record in research_attachments
        ]
        if research_draft.strip():
            research_rows.insert(0, "DRAFT: " + research_draft.strip()[:120])
        self._populate_list(
            self.research_sources_list,
            research_rows,
            "No Research sources/materials queued.",
        )
        self.research_handoff_button.setText(
            "Thread Handoff Package (Recommended)"
            if research_pressure.should_prepare_handoff
            else "Thread Handoff Package"
        )

        (
            _core_conversation,
            core_draft,
            core_attachments,
            core_pressure,
            core_route,
        ) = self._department_workspace_snapshot("core")
        self.core_status_label.setText(
            f"Thread pressure: {core_pressure.level.value} · "
            f"~{core_pressure.estimated_tokens:,} tokens · "
            f"Attachments: {len(core_attachments)} · Route: {core_route}. "
            f"{core_pressure.handoff_recommendation}"
        )
        core_rows = [
            item.original_filename for item in downloads.get("core", [])[:8]
        ]
        if core_draft.strip():
            core_rows.insert(0, "DRAFT: " + core_draft.strip()[:120])
        self._populate_list(
            self.core_outputs_list,
            core_rows,
            "No Core outputs captured.",
        )
        self.core_handoff_button.setText(
            "Thread Handoff Package (Recommended)"
            if core_pressure.should_prepare_handoff
            else "Thread Handoff Package"
        )

    def refresh(self) -> None:
        """Reload the operator surface from durable local state."""

        conversations = self.state_store.load_operational_conversations()
        exchanges = self.state_store.load_browser_exchanges()
        handoffs = self.state_store.load_handoffs()
        downloads = {
            department_id: self.state_store.load_generated_downloads(department_id)
            for department_id, _ in _DEPARTMENTS
        }
        self._refresh_department_workspaces(downloads)

        attention_rows: list[str] = []
        for record in conversations:
            if record.status not in _ATTENTION_OPERATIONAL_STATUSES:
                continue
            if record.status == "RESULT_READY":
                kind = "RESULT READY — acknowledge & close"
            else:
                kind = record.attention_kind or record.status
            reason = (
                f" — {record.attention_reason}"
                if record.attention_reason
                else ""
            )
            attention_rows.append(f"{kind}: {record.title}{reason}")

        for record in exchanges:
            if record.state not in _RECOVERY_BROWSER_STATES:
                continue
            disposition = record.recovery_disposition or "review required"
            attention_rows.append(
                f"Browser {record.department_id}: {record.state} — {disposition}"
            )

        for record in handoffs:
            if record.status not in _ATTENTION_HANDOFF_STATUSES:
                continue
            if record.status is HandoffStatus.HELD:
                action = "review or stop"
            elif record.status is HandoffStatus.RETURNED:
                action = "close or continue"
            elif record.status in {
                HandoffStatus.ANSWERED,
                HandoffStatus.AWAITING_USER_DECISION,
            }:
                action = "operator decision required"
            elif record.status is HandoffStatus.PENDING_APPROVAL:
                action = "approval required"
            else:
                action = "review required"
            attention_rows.append(
                "HANDOFF "
                f"{record.status.value.upper()} — {action}: "
                f"{record.source_department_id} → {record.target_department_id}"
            )

        active_rows: list[str] = []
        for record in conversations:
            if record.status in _ACTIVE_OPERATIONAL_STATUSES:
                participants = " ↔ ".join(record.participants)
                active_rows.append(
                    f"{record.status}: {record.title} [{participants}]"
                )

        for record in handoffs:
            if record.status in _ACTIVE_HANDOFF_STATUSES:
                active_rows.append(
                    "HANDOFF "
                    f"{record.status.value}: {record.source_department_id} → "
                    f"{record.target_department_id}"
                )

        active_exchange_count = sum(
            record.state in _ACTIVE_BROWSER_STATES for record in exchanges
        )
        recovery_exchange_count = sum(
            record.state in _RECOVERY_BROWSER_STATES for record in exchanges
        )

        department_rows: list[str] = []
        for department_id, display_name in _DEPARTMENTS:
            active_count = sum(
                record.status in _ACTIVE_OPERATIONAL_STATUSES
                and department_id in record.participants
                for record in conversations
            ) + sum(
                record.status in _ACTIVE_HANDOFF_STATUSES
                and department_id
                in {record.source_department_id, record.target_department_id}
                for record in handoffs
            )
            attention_count = sum(
                record.status in _ATTENTION_OPERATIONAL_STATUSES
                and department_id in record.participants
                for record in conversations
            ) + sum(
                record.status in _ATTENTION_HANDOFF_STATUSES
                and department_id
                in {record.source_department_id, record.target_department_id}
                for record in handoffs
            )
            transport_count = sum(
                record.department_id == department_id
                and record.state
                in (_ACTIVE_BROWSER_STATES | _RECOVERY_BROWSER_STATES)
                for record in exchanges
            )
            output_count = len(downloads[department_id])
            if attention_count:
                state = "ATTENTION"
            elif active_count or transport_count:
                state = "ACTIVE"
            else:
                state = "IDLE"
            department_rows.append(
                f"{display_name}: {state} · work {active_count} "
            f"· attention {attention_count} "
                f"· transport {transport_count} · files {output_count}"
            )

        result_rows: list[str] = []
        for record in conversations:
            if record.status == "RESULT_READY":
                result_rows.append(f"RESULT: {record.title}")
            if len(result_rows) >= 6:
                break

        recent_downloads = sorted(
            (item for records in downloads.values() for item in records),
            key=lambda item: item.captured_at,
            reverse=True,
        )
        for item in recent_downloads[:6]:
            result_rows.append(
                f"FILE [{item.department_id}]: {item.original_filename}"
            )

        attention_counts = Counter(
            record.attention_kind or record.status
            for record in conversations
            if record.status in _ATTENTION_OPERATIONAL_STATUSES
        )
        attention_total = len(attention_rows)
        active_total = len(active_rows)
        output_total = sum(len(records) for records in downloads.values())

        self._set_card_value(self.attention_summary, str(attention_total))
        self._set_card_value(self.active_summary, str(active_total))
        bridge_text = (
            f"{active_exchange_count} active"
            if active_exchange_count
            else "Idle"
        )
        if recovery_exchange_count:
            bridge_text += f" · {recovery_exchange_count} recovery"
        self._set_card_value(self.bridge_summary, bridge_text)
        self._set_card_value(self.output_summary, str(output_total))

        self._populate_list(
            self.attention_list,
            attention_rows,
            "No operator attention required.",
        )
        self._populate_list(
            self.active_list,
            active_rows,
            "No active background work.",
        )
        self._populate_list(
            self.department_list,
            department_rows,
            "No department state available.",
        )
        self._populate_list(
            self.result_list,
            result_rows,
            "No recent results or generated files.",
        )

        details = []
        for key, label in (
            ("OPERATOR_DECISION", "decisions"),
            ("BLOCKER", "blockers"),
            ("RESULT", "results"),
        ):
            if attention_counts.get(key):
                details.append(f"{attention_counts[key]} {label}")
        suffix = " · ".join(details) if details else "no review queue"
        self.footer_label.setText(
            "B8C.1 prototype: Project-first operator workspace with independent "
            "Project, Core and Research continuity controls. Research source intake "
            "and repository writes remain operator-controlled. "
            f"Operational review: {suffix}."
        )
