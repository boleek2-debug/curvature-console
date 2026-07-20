# CURVATURE CONSOLE — SOURCE OVERVIEW

Status: Active
Version: 1.2.0
Owner: Project Curvature
Repository: `~/curvature-console`
Last Updated: 2026-07-20

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
Completed: ASSISTANT-001B5.2B — Browser Lifecycle and One-Click UX
Completed: ASSISTANT-001B5.2C — Durable URL-Only Conversation Routing
Next:      ASSISTANT-001B5.2D — Generated File Download Capture
```

Current verification:

```text
56 automated tests passed
live Core response: PROJECT_SCOPED_ROUTE_OK
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
