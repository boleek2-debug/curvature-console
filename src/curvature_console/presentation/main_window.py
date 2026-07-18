"""Main three-panel desktop window for Curvature Console."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
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
from curvature_console.infrastructure.context_loader import (
    ContextLoadResult,
    WorkspaceContextLoader,
)
from curvature_console.presentation.context_preview_dialog import (
    ContextPreviewDialog,
)
from curvature_console.presentation.department_panel import DepartmentPanel


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
        self.context_loader = WorkspaceContextLoader()
        self.workspace_configs: dict[str, WorkspaceConfig] = {}
        self.context_results: dict[str, ContextLoadResult] = {}

        self._focused_department_id: str | None = None
        self._three_panel_sizes = [500, 500, 500]

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("departmentSplitter")
        self.splitter.setChildrenCollapsible(False)

        self.department_panels: dict[str, DepartmentPanel] = {}

        for department_id, title, responsibility in self.DEPARTMENT_DEFINITIONS:
            panel = DepartmentPanel(
                department_id=department_id,
                title=title,
                responsibility=responsibility,
            )
            panel.focus_requested.connect(self.focus_department)
            panel.context_refresh_requested.connect(self.refresh_context)
            panel.context_preview_requested.connect(self.preview_context)
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
        status_bar.showMessage("Three departments operational — AI not connected")
        self.setStatusBar(status_bar)

        self.load_workspace_configs()
        self.refresh_all_contexts()

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

    def focus_department(self, department_id: str) -> None:
        """Temporarily show one department without destroying other state."""
        if department_id not in self.department_panels:
            raise ValueError(f"Unknown department: {department_id}")

        if self._focused_department_id is None:
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

    def restore_three_panel_view(self) -> None:
        """Restore all three department panels and their previous widths."""
        for panel in self.department_panels.values():
            panel.setVisible(True)

        self._focused_department_id = None
        self.splitter.setSizes(self._three_panel_sizes)
        self.restore_button.setEnabled(False)
        self.statusBar().showMessage(
            "Three departments operational — AI not connected"
        )
