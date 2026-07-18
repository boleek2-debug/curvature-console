# CHANGELOG

Status: Active
Version: 0.2.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# Purpose

This document records completed and verified Curvature Console work only.

---

## 2026-07-18

### ASSISTANT-001B1 — Repository and Application Foundation

Completed

- standalone `curvature-console` repository
- dedicated Conda environment
- Python package foundation
- PySide6 application entry point
- minimal desktop main window
- reproducible environment definition
- automated application tests
- initial README, HANDOFF, ROADMAP and CHANGELOG

Verified

- Python 3.11.15
- package installed in editable mode
- PySide6 loaded from the Conda environment
- 2 automated tests passed
- desktop application launched successfully
- window title displayed `Curvature Console`

Environment decision

- PySide6 and Qt are installed through Conda Forge
- Curvature Console is installed through pip with `--no-deps`
- pip-provided PySide6 is not used on the verified Linux environment

Result

Curvature Console now has a separate, reproducible and testable desktop application foundation ready for the three-panel interface sprint.
