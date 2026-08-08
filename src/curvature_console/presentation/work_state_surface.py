"""Read-only operator work-state surface for Curvature Console."""

from __future__ import annotations

from collections import Counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.handoff import HandoffStatus
from curvature_console.infrastructure.state_store import SQLiteStateStore


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
    """Present durable cross-department work state without mutating it."""

    def __init__(
        self,
        *,
        state_store: SQLiteStateStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state_store = state_store
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
            "Read-only operational overview. Existing department workspaces "
            "remain unchanged."
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
            "B8B prototype: view only — no workflow or repository actions are "
            "performed here."
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

    def refresh(self) -> None:
        """Reload the prototype from durable local state only."""

        conversations = self.state_store.load_operational_conversations()
        exchanges = self.state_store.load_browser_exchanges()
        handoffs = self.state_store.load_handoffs()
        downloads = {
            department_id: self.state_store.load_generated_downloads(department_id)
            for department_id, _ in _DEPARTMENTS
        }

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
            "B8B prototype: view only — no workflow or repository actions are "
            "performed here. "
            f"Operational review: {suffix}."
        )
