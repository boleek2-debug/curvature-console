# Curvature Console Repository

Curvature Console is a standalone internal development coordination application for Project Curvature.

It provides three permanent and equal departmental workspaces:

- Curvature Project
- Curvature Core
- Curvature Research

The application is separate from Curvature Platform, World Core, Chronicle Client and gameplay.

---

# Canonical Console Documentation

Console documents use the `CONSOLE_` prefix so they remain unambiguous when
uploaded together with Project Curvature documents to one ChatGPT Project.

- `CONSOLE_README.md` — source-friendly Console overview
- `CONSOLE_HANDOFF.md` — current state and exact next step
- `CONSOLE_ROADMAP.md` — ordered implementation plan
- `CONSOLE_CHANGELOG.md` — completed and verified work
- `CONSOLE_DECISIONS.md` — durable architecture decisions
- `CONSOLE_PIPELINE.md` — development and verification process

`README.md` remains the standard repository landing page.

---

# Current State

The following work is complete and verified:

- ASSISTANT-001B1 — Repository and Application Foundation
- ASSISTANT-001B2 — Three-Panel Desktop Shell
- Per-Department Attachment Queues
- ASSISTANT-001B3 — Workspace Configuration and Context Loading
- ASSISTANT-001B4 — Local State and Conversation Persistence
- ASSISTANT-001B5.1 — Task and Thread Handoff Packages
- ASSISTANT-001B5.2A — Browser Bridge Foundation
- ASSISTANT-001B5.2B — Browser Lifecycle and One-Click UX
- ASSISTANT-001B5.2C — Durable URL-Only Conversation Routing

Current verification:

```text
56 automated tests passed
live Core response: PROJECT_SCOPED_ROUTE_OK
```

The next implementation unit is:

```text
ASSISTANT-001B5.2D — Generated File Download Capture
```

---

# Product Model

Curvature Console is a local coordination, context, persistence, routing and browser-automation tool.

One shared official ChatGPT Project remains the AI conversation environment:

```text
ChatGPT Project: Curvature
├── Project department conversation
├── Core department conversation
└── Research department conversation
```

Routing uses `department_id` and the persisted active conversation URL. Conversation titles are not routing identifiers.

Curvature Console prepares a controlled Task Package or Thread Handoff Package, sends it automatically through the matching logged-in ChatGPT Project, retrieves the completed assistant response and routes it back to the originating Console department.

Manual copy-and-paste is not an accepted product workflow.

---

# Cost Rule

Curvature Console must not create additional mandatory AI costs beyond the user's existing ChatGPT Plus subscription.

Therefore:

- paid OpenAI API usage is not part of the default architecture;
- no OpenAI API key is required;
- no paid provider request is performed;
- no background process may incur API, token, tool or search charges;
- official ChatGPT remains the AI conversation environment;
- browser automation uses the user's existing logged-in ChatGPT Plus session;
- any future paid provider integration requires a separate explicit decision and must be optional and disabled by default.

The authoritative decisions are recorded in `CONSOLE_DECISIONS.md`.

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

## Controlled transfer packages

Task Packages are used for normal work in an existing department chat.

Thread Handoff Packages are used when starting a new chat in the same department's ChatGPT Project.

The package builder provides:

- department identity and authority;
- full department role;
- mode-specific repository context;
- bounded recent local conversation;
- current task;
- attachment manifest;
- response instructions.

B5.1 originally exposed clipboard delivery. That delivery method is superseded by the automated browser bridge. The package builder itself remains the approved payload source.

## Browser bridge foundation

B5.2A provides:

- Playwright as an explicit dependency;
- ordinary Google Chrome startup with a dedicated local profile;
- local Chrome DevTools Protocol endpoint;
- CDP connection lifecycle;
- explicit department-to-project mapping;
- read-only login and project probe;
- browser-profile exclusion from Git;
- unit tests without live network access.

Verified live automation proof:

```text
ordinary Chrome
→ logged-in ChatGPT Plus session
→ Curvature Core navigation
→ automatic message entry
→ automatic send
→ response completion detection
→ exact response extraction
```

Verified response:

```text
CURVATURE_AUTOMATION_OK
```

---

# Browser Runtime

Chrome executable:

```text
/usr/bin/google-chrome-stable
```

Dedicated local profile:

```text
~/curvature-console/data/browser-profile/
```

CDP endpoint:

```text
http://127.0.0.1:9222
```

The browser profile contains private session data and must never be committed.

Start ordinary Chrome manually during development:

```bash
cd ~/curvature-console

google-chrome-stable \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/curvature-console/data/browser-profile" \
  --no-first-run \
  --no-default-browser-check \
  https://chatgpt.com
```

The user performs login manually inside this dedicated profile. Passwords and authentication tokens are never stored in Console source code.

---

# Department Routing

```text
project  → persisted project conversation URL
core     → persisted core conversation URL
research → persisted research conversation URL
```

A task and its response must remain bound to the same department. Mutable ChatGPT titles and sidebar labels are never used as routing keys.

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

Playwright is installed as a Python package dependency. The browser bridge controls the system Google Chrome installation through CDP; it does not require the bundled Playwright Chromium for the approved runtime.

Verified environment:

```text
Conda:
- Python 3.11
- PySide6
- PyYAML
- pytest

pip:
- Curvature Console editable package
- Playwright dependency
```

---

# Create the Environment

```bash
conda env create -f environment.yml
conda activate curvature-console
python -m pip install -e .
```

---

# Repair or Update an Existing Environment

```bash
conda activate curvature-console

conda install -c conda-forge \
  pyside6 \
  pyyaml \
  pytest \
  xcb-util-cursor \
  libxcb \
  xorg-libxcursor \
  -y

python -m pip install -e .
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

Live browser verification is separate from the unit suite and must only run when ordinary Chrome is open with the dedicated profile and CDP port.

---

# Active Milestone

## ASSISTANT-001B5 — ChatGPT Plus Browser Integration

Completed and verified:

```text
ASSISTANT-001B5.2B — Browser Lifecycle and One-Click UX
ASSISTANT-001B5.2C — Durable URL-Only Conversation Routing
```

Next:

```text
ASSISTANT-001B5.2D — Generated File Download Capture
```

See `CONSOLE_ROADMAP.md`, `CONSOLE_HANDOFF.md`, `CONSOLE_DECISIONS.md` and `CONSOLE_PIPELINE.md`.


# Next Browser Workflow Milestones

- B5.2D — generated-file download capture and Download Inbox;
- B5.2E — Package Review, path validation, backups, explicit Apply and Git diff;
- B5.3 — structured department conversation and exchange records.
