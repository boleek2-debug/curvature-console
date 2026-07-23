# CURVATURE CONSOLE — CURRENT STATE

Status: Active
Last Updated: 2026-07-23
Repository: `~/curvature-console`
Branch: `main`
Current pushed commit: `817860e Add generated file download capture`

---

# Purpose

This document is the concise operational source of truth for Curvature Console.

The same canonical Console documents are used:

- locally by Curvature Console;
- as uploaded copies in the shared ChatGPT Project `Curvature` Sources.

---

# Verified Baseline

```text
69 automated tests passed
git diff --check passed
commit 817860e pushed
main == origin/main
working tree clean
```

---

# Source Model

Curvature Console loads two distinct authoritative source roots:

```text
console   → ~/curvature-console
curvature → ~/Curvature
```

Console-specific state, roles, decisions and implementation planning remain in:

```text
~/curvature-console
```

Project Curvature vision, architecture, world, language and project state remain
in:

```text
~/Curvature
```

Every loaded document retains its source label in Context Preview.

Verified context counts:

```text
Project  — 8 loaded · 0 errors
Core     — 10 loaded · 0 errors
Research — 8 loaded · 0 errors
```

---

# Department Routing State

All three departments use dedicated Console-only conversations inside the one
shared ChatGPT Project named `Curvature`.

Verified:

```text
Core      — route and restart persistence verified
Project   — PROJECT_ROUTE_OK
Project   — PROJECT_RESTART_ROUTE_OK
Research  — RESEARCH_ROUTE_OK
Research  — RESEARCH_RESTART_ROUTE_OK
```

Routing remains:

```text
department_id
→ persisted active_conversation_url
```

Conversation titles and sidebar order are never routing keys.

---

# Completed Browser-Bridge State

Implemented and verified:

- immutable request identifiers;
- request-bound department identifiers;
- exact persisted conversation URLs;
- one dedicated request page per exchange;
- visible request-marker confirmation;
- exact new-response capture;
- originating-panel-only response delivery;
- explicit failure on request-page closure;
- no false response persistence;
- task-draft preservation after failure;
- preservation of unrelated Chrome sessions;
- lightweight normal Task payload;
- full continuity reserved for Thread Handoff.

---

# Completed B5.2D — Generated File Download Capture

Delivered and live-verified:

- response-scoped generated-file control detection;
- support for rendered JavaScript-only file controls without normal `href`;
- request URL capture before Chrome native Save As handling;
- authenticated file retrieval through the active browser session;
- no required manual Save As workflow;
- Console Download Inbox outside both repositories;
- original filename preservation;
- collision-safe filenames;
- non-empty response validation;
- atomic file write;
- SQLite metadata persistence;
- department, request and conversation association;
- per-department Downloads list;
- restart persistence;
- immediate UI refresh after successful registration;
- restoration of the dedicated conversation after request interception.

Download Inbox:

```text
~/.local/share/curvature-console/download-inbox/
```

Live verification:

```text
generated file: core-download-test.zip
saved collision-safe file: core-download-test(7).zip
ZIP size: 155 bytes
contained file: verification.txt
contained text: CORE_DOWNLOAD_CAPTURE_OK
Downloads counter increased after a second capture
download record survived Console restart
no final chrome-error://chromewebdata/ route warning
```

---

# Current Milestone

```text
ASSISTANT-001B5.2E — Package Review and Safe Apply
```

B5.2E must preserve the trust boundary established by B5.2D:

```text
ChatGPT generated file
→ Console Download Inbox
→ Package Review
→ explicit user approval
→ safe repository application
→ Git diff
```

No automatic commit or push is permitted.

---

# Strategic Direction

Curvature Console is expected to grow into the central control plane for the
whole Curvature project.

That direction does not mean one module performs all work. Console coordinates,
observes, validates and records the work of specialised modules.

A future unified operation trace must connect:

```text
request
→ department
→ conversation
→ source context
→ response
→ generated files
→ package review
→ repository application
→ tests
→ Git state
→ final result
```

This is a strategic architecture direction, not permission to bypass current
milestone boundaries.

---

# Exact Next Step

1. Start `ASSISTANT-001B5.2E — Package Review and Safe Apply`.
2. Inspect the current repository before implementation.
3. Define the machine-readable package manifest contract.
4. Validate repository identity and repository-relative paths.
5. reject absolute paths, traversal, unsafe ZIP entries and escaping symlinks.
6. classify Create, Replace, Conflict and Skip actions.
7. provide a complete Package Review screen.
8. require one explicit Apply approval.
9. back up replaced files.
10. show the post-apply Git diff.
11. do not commit or push automatically.
