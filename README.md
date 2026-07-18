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
- ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Current verification result:

```text
32 passed
```

The active implementation unit is:

```text
ASSISTANT-001B5.2 — Assistant Response Import
```

---

# Product Model

Curvature Console is a local coordination, context, persistence and transfer tool.

It does not replace the official ChatGPT application.

Recommended ChatGPT structure:

```text
ChatGPT Project: Curvature Project
ChatGPT Project: Curvature Core
ChatGPT Project: Curvature Research
```

Normal work uses a compact Task Package.

Moving to a new chat inside the same ChatGPT Project uses a comprehensive Thread Handoff Package.

---

# Cost Rule

Curvature Console must not create additional mandatory AI costs beyond the user's existing ChatGPT Plus subscription.

Therefore:

- paid OpenAI API usage is not part of the default architecture;
- no OpenAI API key is required;
- no automatic paid model request is performed;
- no background process may incur token, tool or search charges;
- official ChatGPT remains the primary AI conversation environment;
- any future paid provider integration requires a separate explicit decision and must be optional and disabled by default.

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

## Task Package

Used for normal work in the current ChatGPT thread.

Includes:

- department identity and authority;
- full role;
- bounded beginning-and-end excerpts from long non-role documents;
- newest 8,000 characters of local conversation;
- current task;
- attachment manifest;
- response instructions.

Long non-role documents are bounded to 4,000 characters per document.

## Thread Handoff Package

Used when moving to a new chat in the same department's ChatGPT Project.

Includes:

- department identity and authority;
- full role;
- full loaded documents;
- newest 24,000 characters of local conversation;
- current task;
- attachment manifest;
- explicit continuity instructions.

Both package types:

- are previewed before copying;
- are copied exactly to the system clipboard;
- perform no network request;
- invoke no paid API.

---

# Repository Boundaries

Curvature Console repository:

```text
~/curvature-console
```

Project Curvature repository:

```text
~/Curvature
```

During the MVP, Curvature Console access to Project Curvature remains read-only.

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
32 passed
```

---

# Active Milestone

## ASSISTANT-001B5 — ChatGPT Plus Workflow Integration

Next implementation unit:

```text
ASSISTANT-001B5.2 — Assistant Response Import
```

Planned behavior:

- select the target department;
- paste or import the assistant response;
- preview it before acceptance;
- preserve the original text;
- append it to the correct local department state;
- persist it locally;
- never send it over the network;
- never invoke a paid API.

See `ROADMAP.md`, `HANDOFF.md` and `DECISIONS.md`.
