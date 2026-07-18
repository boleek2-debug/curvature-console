# Curvature Console

Curvature Console is a standalone internal development coordination application for Project Curvature.

It provides three permanent and equal departmental workspaces:

- Curvature Project
- Curvature Core
- Curvature Research

The application is separate from Curvature Platform, World Core, Chronicle Client and gameplay.

---

# Current State

The following work is complete and verified:

- ASSISTANT-001B1 — Repository and Application Foundation
- ASSISTANT-001B2 — Three-Panel Desktop Shell
- Per-Department Attachment Queues
- ASSISTANT-001B3 — Workspace Configuration and Context Loading
- ASSISTANT-001B4 — Local State and Conversation Persistence

Current verification result:

```text
22 passed
```

Latest implementation commit:

```text
2eec4e6 Implement ASSISTANT-001B4 local state persistence
```

The active milestone is:

```text
ASSISTANT-001B5 — ChatGPT Plus Workflow Integration
```

---

# Product Model

Curvature Console is a local coordination, context, persistence and transfer tool.

It does not replace the official ChatGPT application.

The intended workflow is:

```text
Curvature Console
→ select a department
→ prepare a department-specific transfer package
→ copy the package to the clipboard
→ continue the conversation in official ChatGPT under the existing Plus subscription
→ copy the assistant response
→ paste or import the response into the correct department workspace
→ persist the local state in SQLite
```

---

# Cost Rule

Curvature Console must not create additional mandatory AI costs beyond the user's existing ChatGPT Plus subscription.

Therefore:

- paid OpenAI API usage is not part of the default architecture;
- Curvature Console must not require an OpenAI API key;
- Curvature Console must not perform automatic paid model requests;
- no background process may incur token, tool or search charges;
- the official ChatGPT interface remains the primary AI conversation environment;
- any future paid provider integration would require a separate explicit project decision and must remain optional and disabled by default.

The authoritative decision is recorded in `DECISIONS.md`.

---

# Implemented Capabilities

## Three-department desktop shell

- simultaneous Project, Core and Research panels;
- resizable horizontal splitter;
- single-department Focus mode;
- restoration of the three-panel layout.

## Workspace context

- YAML workspace definitions;
- Markdown department roles;
- read-only access to the Project Curvature repository;
- automatic loading of configured documents;
- context preview;
- manual context refresh.

## Attachments

- independent attachment queues per department;
- file selection;
- screenshot paste;
- drag-and-drop;
- persistent screenshot storage;
- attachment metadata persistence.

Attachments are never shared automatically between departments.

## Local persistence

- SQLite operational-state database;
- independent draft and conversation text per department;
- attachment metadata;
- splitter widths;
- Focus state;
- restart continuity.

Operational data is stored under:

```text
~/curvature-console/data/
```

The main database is:

```text
~/curvature-console/data/curvature_console.sqlite3
```

Persistent pasted screenshots are stored under:

```text
~/curvature-console/data/attachments/<department>/
```

Runtime data remains excluded from Git.

---

# Repository Boundaries

The Curvature Console repository is:

```text
~/curvature-console
```

The Project Curvature repository is:

```text
~/Curvature
```

During the MVP, Curvature Console access to the Project Curvature repository remains read-only.

Curvature Console must not:

- edit Project Curvature documents automatically;
- execute Git operations automatically;
- bypass department authority boundaries;
- share attachments between departments without an explicit handoff.

---

# Environment Rule

PySide6 and its Qt runtime must be installed through Conda Forge.

Do not install PySide6 through pip in the verified Linux environment.

The package itself is installed through pip in editable mode with dependency resolution disabled.

```text
Conda:
- Python 3.11
- PySide6
- PyYAML
- pytest

pip:
- Curvature Console package only
- editable installation
- --no-deps
```

---

# Create the Environment

```bash
conda env create -f environment.yml
conda activate curvature-console
```

---

# Repair or Update an Existing Environment

```bash
conda activate curvature-console

conda install -c conda-forge   pyside6   pyyaml   pytest   xcb-util-cursor   libxcb   xorg-libxcursor   -y

python -m pip install -e . --no-deps
```

---

# Run

```bash
python -m curvature_console.main
```

or:

```bash
curvature-console
```

---

# Test

```bash
python -m pytest -v
```

Expected current result:

```text
22 passed
```

---

# Active Milestone

## ASSISTANT-001B5 — ChatGPT Plus Workflow Integration

The milestone must support the existing ChatGPT Plus workflow without paid API usage.

First implementation unit:

```text
ASSISTANT-001B5.1 — ChatGPT Transfer Package
```

Planned behavior:

- select one department;
- assemble its role, loaded context, local conversation state, draft and attachment manifest;
- format a bounded transfer package;
- preview the package;
- copy it to the system clipboard;
- never send it over the network;
- never invoke a paid API.

See `ROADMAP.md`, `HANDOFF.md` and `DECISIONS.md`.
