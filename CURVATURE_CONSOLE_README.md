# CURVATURE CONSOLE — SOURCE OVERVIEW

Status: Active
Version: 1.2.0
Owner: Project Curvature
Repository: `~/curvature-console`
Last Updated: 2026-07-23

---

# Purpose

This is the preferred Curvature Console overview for shared ChatGPT Project
Sources. The `CONSOLE_` namespace prevents collisions with documentation from
the separate `~/Curvature` repository.

# Canonical Reading Order

1. `CONSOLE_HANDOFF.md`
2. `CONSOLE_DECISIONS.md`
3. `CONSOLE_ROADMAP.md`
4. `CONSOLE_CHANGELOG.md`
5. `CONSOLE_PIPELINE.md`
6. `CONSOLE_README.md`

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
Core verified: ASSISTANT-001B5.2R — Deterministic Browser Bridge Rewrite
Rollout next: dedicated Project and Research conversations
Paused: ASSISTANT-001B5.2D — Generated File Download Capture
```

Current verification:

```text
61 automated tests passed
live Core responses:
- CORE_BRIDGE_REWRITE_OK
- CORE_RESTART_ROUTE_OK
- CORE_SECOND_REQUEST_OK
controlled request-page closure: explicit failure, no false response stored
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

Core is the first verified operational department. Project and Research are
activated only after their own dedicated conversations receive full Thread
Handoffs and their routes pass live verification.

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
