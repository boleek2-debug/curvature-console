# CURVATURE CONSOLE CHANGELOG

Status: Active
Version: 0.9.0
Owner: Project Curvature
Last Updated: 2026-07-23

---

## 2026-07-23

### ASSISTANT-001B5.2D — Generated File Download Capture

Completed, live-verified, committed and pushed.

Commit:

```text
817860e Add generated file download capture
```

Delivered:

- generated-file detection scoped to the new assistant response;
- support for rendered JavaScript-only file controls;
- generated-file request URL capture;
- authenticated browser-session retrieval;
- Console Download Inbox outside both repositories;
- original filename preservation;
- collision-safe filenames;
- non-empty body validation;
- atomic writes;
- SQLite generated-download records;
- request, department and conversation linkage;
- per-department Downloads list;
- immediate UI refresh;
- restart persistence;
- conversation restoration after request interception.

Verified:

```text
69 automated tests passed
git diff --check passed
core-download-test(7).zip
155 bytes
verification.txt
CORE_DOWNLOAD_CAPTURE_OK
Downloads counter increased after a second capture
download record survived Console restart
no final chrome-error://chromewebdata/ warning
main == origin/main
working tree clean
```

Result:

Curvature Console can now receive a generated file from the active ChatGPT
response, store it safely outside the repositories, preserve provenance, and
show the persistent record in the correct department panel without requiring a
manual Save As workflow.

---

## 2026-07-23

### ASSISTANT-001B5.2C5 / B5.2R — Lightweight Deterministic Core Workflow

Implemented and Core-verified.

Delivered:

- lightweight normal Task payload;
- full context reserved for Thread Handoff;
- immutable request identifiers;
- dedicated request page per exchange;
- exact persisted conversation routing;
- request marker confirmation;
- request-bound response delivery;
- rejection of stale or foreign results;
- explicit failure when the request page closes;
- preservation of the task draft after failure;
- dedicated Console-only Core conversation;
- hybrid browser ownership lifecycle.

Verified:

```text
61 automated tests passed
git diff --check passed
CORE_BRIDGE_REWRITE_OK
CORE_RESTART_ROUTE_OK
CORE_SECOND_REQUEST_OK
controlled request-page closure failed explicitly
false response was not stored
unrelated Chrome session remained open
```

Result:

Curvature Console now has a deterministic and restart-safe Core workflow. The
same model is ready to be rolled out to dedicated Project and Research
conversations after the Core Thread Handoff is accepted.

B5.2D remains paused until all three department routes pass live verification.

---

## 2026-07-20

### ASSISTANT-001B5.2B / B5.2C — Reliable One-Click Browser Routing

Completed, verified and pushed.

Delivered:

- normal Task sending in one click;
- one confirmation only for Thread Handoff;
- independent department-panel availability during an exchange;
- explicit browser lifecycle stages and recoverable failures;
- cleanup of Console-owned browser processes;
- visible Chrome fallback after headless rendering failure;
- automatic response retrieval and SQLite persistence;
- one shared ChatGPT Project architecture;
- URL-only routing by department;
- removal of conversation-title routing;
- persisted active conversation URL and URL history;
- support for direct `/c/<id>` routes;
- support for project-scoped `/g/<project-id>/c/<id>` routes;
- shared Project URL reserved for new conversations.

Verified:

- UI no longer remains indefinitely at `WAITING FOR CHATGPT` when the browser fails;
- only the active department panel is disabled;
- Project and Research remain usable while Core is sending;
- actual observed project-scoped URL was captured before changing validation;
- successful Core live response: `PROJECT_SCOPED_ROUTE_OK`;
- complete automated suite: `56 passed`;
- implementation closeout present in clean commit `b557ce6eb5556277d0b65114b3f5893c302d78b2`.

Result:

Curvature Console can send a normal Task to the persisted department conversation, retrieve the response and restore the originating panel without using mutable conversation titles or the paid OpenAI API.

---

# Purpose

This document records completed and verified Curvature Console work and accepted architecture decisions.

---

## 2026-07-19

### CONSOLE-DOCS-001 — Documentation Namespace Migration

Completed:

- namespaced canonical Console documents with the `CONSOLE_` prefix;
- preserved standard root `README.md`;
- added `CONSOLE_README.md` for shared ChatGPT Project Sources;
- updated Console cross-document references;
- retained main-repository names in workspace configuration and intentional
  test fixtures.

Result:

Project Curvature and Curvature Console documentation can coexist in one
ChatGPT Project without filename ambiguity.

---

## 2026-07-18

### ASSISTANT-001B5.2A — Browser Bridge Foundation

Completed and verified.

Commit:

```text
a33fa4e Implement B5.2A browser bridge foundation
```

Delivered:

- Playwright dependency declared in `pyproject.toml`;
- `BrowserBridgeConfig`;
- ordinary Google Chrome launcher;
- dedicated local browser-profile path;
- localhost CDP endpoint configuration;
- Playwright CDP connection lifecycle;
- explicit Project/Core/Research mapping;
- read-only connection, login and project probe;
- runtime browser profile excluded from Git;
- unit tests without live ChatGPT dependency;
- updated HANDOFF and ROADMAP architecture.

Department mapping:

```text
project  → Curvature Project
core     → Curvature Core
research → Curvature Research
```

Live proof completed before implementation:

```text
ordinary Chrome
→ persistent local profile
→ CDP connection
→ logged-in ChatGPT Plus
→ Curvature Core navigation
→ automatic message entry
→ automatic send
→ response completion detection
→ exact response extraction
```

Verified assistant response:

```text
CURVATURE_AUTOMATION_OK
```

The complete automated proof required no manual copy or paste.

Result:

Curvature Console now has a tested foundation for automated ChatGPT Plus interaction without the paid OpenAI API.

### Architecture Decision — Automated ChatGPT Browser Bridge

Accepted:

- manual copy-paste is rejected as a product workflow;
- the package builder remains the controlled payload source;
- ordinary logged-in Chrome is controlled locally through CDP;
- Playwright provides browser automation;
- browser profile and session data remain local;
- each response must return to its originating department;
- failures must be explicit for login expiry, CAPTCHA, timeout and UI changes;
- user-triggered automation is required during the MVP.

Recorded in:

```text
CONSOLE_DECISIONS.md — ADR-004
CONSOLE_DECISIONS.md — ADR-005
```

### ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Completed and verified.

Commit:

```text
c4e1bd1 Implement B5.1 ChatGPT transfer packages
```

Delivered:

- deterministic local package builder;
- compact Task Package;
- comprehensive Thread Handoff Package;
- full department role inclusion;
- department identity and authority rules;
- bounded document excerpts for Task Packages;
- full loaded context for Thread Handoff Packages;
- bounded recent local conversation;
- current task inclusion;
- attachment manifest;
- package preview;
- exact clipboard copy.

Task Package limits:

```text
Long non-role document: 4,000 characters
Recent local conversation: 8,000 characters
```

Thread Handoff Package limits:

```text
Recent local conversation: 24,000 characters
Loaded documents: full content
```

The clipboard delivery UI is superseded as the product path by B5.2 browser automation. The deterministic package builder remains active.

Related Project Curvature documentation commit:

```text
10ed638 Align Console architecture with ChatGPT Plus workflow
```

### Architecture Decision — Zero Additional AI Cost

Accepted:

- Curvature Console must not require AI spending beyond the user's existing ChatGPT Plus subscription;
- the paid OpenAI API is excluded from the default MVP architecture;
- no API key is required;
- no automatic paid provider request is allowed.

The manual workflow portion was later superseded by ADR-004 while the zero-cost rule remained active.

Recorded in:

```text
CONSOLE_DECISIONS.md — ADR-002
```

### ASSISTANT-001B4 — Local State and Conversation Persistence

Completed and verified.

Commit:

```text
2eec4e6 Implement ASSISTANT-001B4 local state persistence
```

### ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed and verified.

Commit:

```text
a934032 Implement ASSISTANT-001B3 workspace context loading
```

### Per-Department Attachments

Completed and verified.

Commit:

```text
8920117 Add per-department attachment queues
```

### ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified.

Commit:

```text
c0085bd Implement ASSISTANT-001B2 three-panel desktop shell
```

### ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified.

Commit:

```text
a6b46f2 Complete ASSISTANT-001B1 application foundation
```

Environment decision:

- PySide6 and Qt are installed through Conda Forge;
- Curvature Console is installed in editable mode;
- Playwright is an explicit Python dependency;
- the approved browser runtime is system Google Chrome controlled through CDP.
