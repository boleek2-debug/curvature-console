# HANDOFF

Status: Ready for Next Sprint
Version: 0.2.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# 1. Completed Sprint

ASSISTANT-001B1 — Repository and Application Foundation

Completed:

- separate `~/curvature-console` repository
- dedicated `curvature-console` Conda environment
- Python 3.11.15
- package foundation
- PySide6 application entry point
- minimal desktop main window
- reproducible environment definition
- automated application tests
- repository documentation foundation

Verified:

- `python -m pytest -v`
- 2 automated tests passed
- `python -m curvature_console.main`
- desktop window opened successfully
- application title displayed `Curvature Console`

# 2. Linux Qt Environment Decision

The working PySide6 runtime is installed through Conda Forge.

Do not install PySide6 through pip in this environment.

Reason:

The pip-provided Qt runtime failed to load the Linux `xcb` platform plugin because of incompatible or unavailable XCB cursor libraries.

The verified configuration is:

- PySide6 from Conda Forge
- Qt runtime from Conda Forge
- XCB support libraries from Conda Forge
- Curvature Console installed with `pip -e . --no-deps`

The VS Code `Error refreshing packages` notification is an editor integration issue and did not block tests or application launch.

# 3. Current Repository

Repository:

```text
~/curvature-console
```

Environment:

```text
curvature-console
```

Project Curvature repository:

```text
~/Curvature
```

Curvature Console repository access remains read-only during the MVP.

# 4. Exact Next Sprint

ASSISTANT-001B2 — Three-Panel Desktop Shell

Goal:

Replace the temporary foundation label with the first real Curvature Console interface.

Required deliverables:

- Project panel
- Core panel
- Research panel
- all three panels visible simultaneously
- horizontal splitter
- equal initial widths
- independent conversation display areas
- independent input areas
- department headers
- visible placeholder status
- resizable panel widths
- temporary panel focus
- return to three-panel view
- automated tests

# 5. Exact Next Step

At the beginning of the next session:

1. read this HANDOFF
2. inspect the current repository tree
3. request the current files that will be modified
4. design the minimum `DepartmentPanel`
5. implement the three-panel shell without adding AI, persistence or context loading

Expected files likely include:

- `src/curvature_console/main.py`
- new presentation package files
- `tests/test_application.py`
- new presentation tests

Do not assume their current content without inspecting them.

# 6. Out of Scope for B2

- OpenAI integration
- context loading
- role document loading
- SQLite
- conversation persistence
- Department State Bus
- handoffs
- Git integration
- repository writes

# 7. Engineering Rules

1. Never guess.
2. Request current files before modifying uncertain code.
3. Deliver complete replacement files.
4. Label every file as replace, create or leave unchanged.
5. One sprint has one goal.
6. Test → Commit → Push.
7. Update HANDOFF after completed work.
8. Code and documentation are written in English.
9. Development discussion is in Polish.
