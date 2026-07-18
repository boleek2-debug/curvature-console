"""Main three-panel desktop window for Curvature Console."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QSplitter,
    QStatusBar,
    QToolBar,
    QWidget,
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
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(application_name)
        self.resize(1500, 850)

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
            self.department_panels[department_id] = panel
            self.splitter.addWidget(panel)

        self.splitter.setSizes(self._three_panel_sizes)
        self.setCentralWidget(self.splitter)

        self.restore_button = QPushButton("Show All Departments")
        self.restore_button.setObjectName("restoreThreePanelButton")
        self.restore_button.clicked.connect(self.restore_three_panel_view)
        self.restore_button.setEnabled(False)

        toolbar = QToolBar("Workspace")
        toolbar.setObjectName("workspaceToolbar")
        toolbar.setMovable(False)
        toolbar.addWidget(self.restore_button)
        self.addToolBar(toolbar)

        status_bar = QStatusBar()
        status_bar.setObjectName("applicationStatusBar")
        status_bar.showMessage("Three departments operational — AI not connected")
        self.setStatusBar(status_bar)

    @property
    def focused_department_id(self) -> str | None:
        """Return the currently focused department, if any."""
        return self._focused_department_id

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
