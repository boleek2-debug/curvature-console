# CURVATURE CONSOLE — SOURCE OVERVIEW

Status: Active
Version: 1.3.0
Owner: Project Curvature
Repository: `~/curvature-console`
Last Updated: 2026-07-23

---

# Purpose

This is the preferred Curvature Console overview for shared ChatGPT Project
Sources. The `CONSOLE_` namespace prevents collisions with documentation from
the separate `~/Curvature` repository.

# Canonical Reading Order

1. `00_CURVATURE_CONSOLE_CURRENT_STATE.md`
2. `CURVATURE_CONSOLE_HANDOFF.md`
3. `CURVATURE_CONSOLE_DECISIONS.md`
4. `CURVATURE_CONSOLE_ROADMAP.md`
5. `CURVATURE_CONSOLE_CHANGELOG.md`
6. `CURVATURE_CONSOLE_PIPELINE.md`
7. `CURVATURE_CONSOLE_README.md`

# Repository Boundary

```text
Curvature Console: ~/curvature-console
Project Curvature: ~/Curvature
```

Curvature Console reads Project Curvature context during the MVP but does not
write that repository or execute Git operations in it.

# Active State

```text
Completed: ASSISTANT-001B5.2C5 — Lightweight Task Delivery
Completed: ASSISTANT-001B5.2R — Deterministic Browser Bridge Rewrite
Completed: Dual-repository workspace context sources
Completed: all three dedicated department routes and restart verification
Completed: ASSISTANT-001B5.2D — Generated File Download Capture
Active next: ASSISTANT-001B5.2E — Package Review and Safe Apply
```

Current verification:

```text
69 automated tests passed
commit 817860e pushed
main == origin/main
working tree clean
Project/Core/Research routes verified after restart
generated ZIP verified with CORE_DOWNLOAD_CAPTURE_OK
download record persisted after restart
```

# Active Architecture

```text
Curvature Console
→ controlled package
→ ordinary logged-in Chrome
→ Playwright over localhost CDP
→ one shared ChatGPT Project: Curvature
→ persisted department conversation URL
→ automatic response retrieval
→ originating Console department
→ SQLite persistence
```

# Routing Rule

```text
department_id
→ active_conversation_url
```

Conversation titles, sidebar labels and visual order are never routing keys.

# Non-Negotiable Rules

- no paid OpenAI API;
- no API key;
- no manual copy-paste product workflow;
- explicit user-triggered sends during the MVP;
- local browser profile and session data;
- strict department routing;
- explicit browser failures;
- test → verify → document → commit → push.


# Approved Next Workflow

```text
one-click Task send
→ automatic response retrieval
→ generated-file download capture
→ Download Inbox
→ Package Review
→ explicit Apply approval
→ backup and repository update
→ Git diff
```

Thread Handoff remains the only send action with a confirmation dialog.


# Task Payload Rule

Normal `Send Task` is lightweight for Project, Core and Research.

It sends the current task, concise department authority and attachment
metadata. It does not resend full project documentation or local conversation
history.

`Send Thread Handoff` remains the comprehensive continuity package.


# Deterministic Browser Request Rule

The browser bridge never uses the currently active or first visible ChatGPT
tab.

Every send operation creates a dedicated request page and binds the complete
exchange to an immutable `request_id` and `department_id`.


# Dedicated Department Conversation Rule

Each Console department uses a dedicated Console-only conversation inside the
shared ChatGPT Project.

Core, Project and Research each have a dedicated Console-only conversation.
All three routes and their restart persistence have passed live verification.

# Hybrid Browser Ownership Rule

The request page is always temporary.

Console may close only browser resources it owns. Existing user browser sessions
remain untouched. Console-owned browser processes may be closed when their
exchange lifecycle ends.


# Dual Repository Context

Every department workspace loads from two named, read-only source roots:

```text
console   → ~/curvature-console
curvature → ~/Curvature
```

Console roles and operational documentation use the canonical
`CURVATURE_CONSOLE_*` files. Project Curvature vision, architecture, language,
world and project-state documents remain authoritative in `~/Curvature`.

Context Preview displays the source identifier for every loaded document.


# Generated File Capture

Generated files are stored outside both repositories:

```text
~/.local/share/curvature-console/download-inbox/
```

A file is registered only after authenticated retrieval, non-empty validation
and atomic write complete successfully. Download records remain isolated by
department and persist across Console restart.

# Strategic Control-Plane Direction

Curvature Console is expected to become the central control plane for the whole
Curvature project.

It will coordinate and observe specialised modules through structured operation
state and a future unified execution ledger. This direction does not replace
domain-specific sources of truth or current milestone boundaries.
