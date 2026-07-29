# CURVATURE CONSOLE CHANGELOG

Status: Active
Version: 0.9.0
Owner: Project Curvature
Last Updated: 2026-07-24

---

## 2026-07-26

### ASSISTANT-001B5.2R — Deterministic Invisible Browser Bridge Repair

Implemented and live-verified. Commit and push pending this closeout.

Delivered:

- lightweight normal Task delivery;
- immutable request identifiers;
- dedicated request page per exchange;
- exact persisted URL routing;
- unique user-message confirmation markers;
- request- and department-bound response delivery;
- stale-result rejection;
- normal Chrome on an invisible Xvfb display;
- per-panel activity heartbeat, stage and elapsed timer;
- timestamped runtime logs;
- selector, route, request and traceback diagnostics;
- process-group cleanup for Console-owned Chrome and Xvfb;
- CDP port release verification.

Verified:

```text
111 automated tests passed
git diff --check passed
Core live request succeeded
user message marker confirmed
assistant response captured
physical Chrome window remained hidden
owned_process_cleanup_complete cdp_port=9222 released=true
```

Next:

```text
ASSISTANT-001B5.R2D2 — General Generated-File Capture
```

The next sprint restores generated-file capture on the rewritten bridge and
supports arbitrary file types without forcing ZIP format.

---


## 2026-07-24

### ASSISTANT-001B5.4 — Thread Pressure and Hybrid Thread Handoff

Completed, verified and pushed.

Delivered:

- independent per-department advisory Thread Pressure;
- GREEN / AMBER / RED states;
- pressure-aware handoff controls;
- RED warning before ordinary task submission;
- contenteditable ChatGPT editor support;
- hybrid Playwright and visible-Chrome lifecycle;
- new-chat creation through the shared ChatGPT Project;
- verified `/c/...` route capture;
- first-response completion handling;
- new-route persistence;
- transcript and pressure reset after verified success;
- preservation of the previous verified state on failure;
- restart-safe operation.

Verified:

```text
118 automated tests passed
git diff --check passed
commit 070eecd pushed
Project context: 8 loaded, 0 errors
Core context: 10 loaded, 0 errors
Research context: 8 loaded, 0 errors
Core live pressure: GREEN → AMBER → RED
Core live Thread Handoff created a new chat
new Core route persisted
Core pressure returned to GREEN
```

Result:

Curvature Console is operational for normal Project Curvature development.
Broad Console feature work is paused until real use demonstrates a need.

### Operational Validation Policy

Accepted:

- shared functionality is implemented once;
- Core receives deep live validation;
- automated tests prove department isolation;
- Project and Research smoke tests are run when a change is department-specific
  or evidence indicates a routing/configuration defect;
- separate live repetition in all three panels is not mandatory for every
  shared implementation.

---

## 2026-07-24

### ASSISTANT-001B5.2E — Package Review and Safe Apply

Completed, live-verified, committed and pushed.

Current pushed repository state:

```text
commit 30cbd3cdef56f4141fe3dbc916592ffe82fefe2d
106 automated tests passed
git diff --check passed
main == origin/main
working tree clean
```

Delivered across E1, E2 and E3:

- validated root package manifest;
- repository identity and path safety;
- CREATE / REPLACE / SKIP / CONFLICT review;
- blocked-package UI;
- one explicit Apply approval;
- mandatory re-review before mutation;
- backup and atomic writes;
- rollback after write failure;
- `APPLY_RESULT.json`;
- post-apply Git status and diff;
- no automatic commit or push.

Live E3 proof applied CREATE, REPLACE and SKIP, verified the backup and metadata,
restored the controlled test changes, and reran the complete test suite.

### Operational Release Scope Decision

Accepted ADR-015. Console feature expansion is paused after mandatory Thread
Pressure, functional Thread Handoff and independent Project/Core/Research
verification. B5.3, the expanded State Bus and the unified execution ledger are
deferred until Project Curvature work requires them.

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


## 2026-07-26 — B5.R2D2 Candidate

Added format-agnostic generated-file capture to the deterministic bridge.

Candidate capabilities:

- assistant-response-scoped file discovery;
- arbitrary extension preservation;
- safe filename handling;
- collision-safe department inbox storage;
- request/department/conversation provenance;
- persistent per-panel download records;
- ZIP-only Package Review remains separate.

## 2026-07-26 — B5.R2D2 File-Card Candidate

Expanded generated-file discovery from assistant text links to the complete
assistant turn, including buttons and file cards. Added bounded runtime DOM
diagnostics for empty captures.

## 2026-07-26 — B5.R2D2 Two-Stage Download Candidate

Added direct-download fallback to file-card preview discovery and activation of
the preview's real Download control.


## 2026-07-27 — B5.R2D2 Citation DOM Diagnostic

Replaced inferred second-stage clicking with bounded before/after DOM evidence.
No follow-up control is selected until the live diagnostic identifies it.


## 2026-07-27 — B5.R2D2 Active-Layer Diagnostic

Replaced the broad first-80-elements snapshot with focused evidence rooted at
the visible Close control and its containing blocking layer.


## 2026-07-27 — B5.R2D2 File-Button Activation

Added bounded fallback activation methods for real generated-file buttons after
live evidence showed that a normal locator click only focused the button.

## 2026-07-28 — Existing File-Card Observer

Added bounded browser-channel instrumentation for one exact generated-file card
to determine whether ChatGPT uses a native download, fetch/XHR, blob URL,
programmatic anchor click or popup.


## 2026-07-28 — B5.R2D2 Fetch-Response Capture

Added direct capture of ChatGPT's successful Estuary attachment response after
TEST-01 confirmed that generated files are delivered through `fetch`, not a
native browser download event.

## 2026-07-28 — ASSISTANT-001B5.R2D2 Closed

- verified real generated `.txt` capture end-to-end in Core;
- confirmed ChatGPT delivery through an Estuary attachment fetch response;
- captured and saved the 29-byte response body under the original filename;
- excluded `Coding Citation` from generated-file activation;
- added recursive Git exclusions for inbox, logs and live-test results;
- made snapshot ZIP creation tolerate pre-1980 file timestamps;
- recorded 128 passing automated tests and clean `git diff --check`.

## 2026-07-29 — ASSISTANT-001B5.5A First Contact Foundation

- added the structured handoff domain model;
- added explicit draft, pending approval, sent, received, answered, closed,
  rejected, held and stopped states;
- added deterministic transition validation;
- added immutable visible correspondence timeline entries;
- added SQLite handoff and timeline persistence;
- added source, target and status indexes and filtering;
- added domain and restart-continuity tests;
- made no UI or browser-send changes.

## 2026-07-29 — ASSISTANT-001B5.5B Bridge Controls

- added a dedicated Bridge Controls dialog;
- added create, edit, request approval, approve, reject, hold, redirect and
  stop controls;
- added the explicit `approved` lifecycle state;
- kept approval separate from browser delivery;
- persisted every control action in the visible correspondence timeline;
- added UI and domain tests;
- added no automatic sends or interdepartmental loops.
