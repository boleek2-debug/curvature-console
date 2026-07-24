# CURVATURE CONSOLE — CURRENT STATE

Status: Active
Last Updated: 2026-07-24
Repository: `~/curvature-console`
Branch: `main`
Current pushed commit: `30cbd3cdef56f4141fe3dbc916592ffe82fefe2d`

---

# Purpose

This document is the concise operational source of truth for Curvature Console.

The same canonical Console documents are used locally by Curvature Console and
as uploaded copies in the shared ChatGPT Project `Curvature` Sources.

---

# Verified Baseline

```text
106 automated tests passed
git diff --check passed
commit 30cbd3c pushed
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

Every loaded document retains its source label in Context Preview.

Verified context counts:

```text
Project  — 8 loaded · 0 errors
Core     — 10 loaded · 0 errors
Research — 8 loaded · 0 errors
```

---

# Department Routing State

Project, Core and Research each use a dedicated Console-only conversation inside
the shared ChatGPT Project named `Curvature`.

All three routes and their restart persistence are verified. Routing remains:

```text
department_id
→ persisted active_conversation_url
```

Conversation titles and sidebar order are never routing keys.

---

# Completed Operational Workflow

The following workflow is implemented and verified:

```text
Task Package
→ deterministic browser exchange
→ exact response retrieval
→ generated-file capture
→ Download Inbox
→ read-only Package Review
→ explicit Apply approval
→ re-review before mutation
→ backup
→ atomic repository writes
→ rollback on failure
→ APPLY_RESULT.json
→ Git status and diff
```

No automatic commit or push is permitted.

Completed package milestones:

```text
B5.2E1 — read-only package review foundation
B5.2E2 — Package Review UI and live CREATE / REPLACE / SKIP / CONFLICT proof
B5.2E3 — explicit safe Apply, backup, rollback and Git report
```

B5.2E3 live verification:

```text
CREATE  b5-2e3-live-create.txt
REPLACE README.md
SKIP    CURVATURE_CONSOLE_ROLE_CORE.md
status  APPLIED
backup  verified
metadata verified
test changes restored
106 automated tests passed
```

---

# Operational Release Boundary

Curvature Console does not need every planned control-plane feature before work
on Project Curvature resumes.

The minimum operational release now requires only:

```text
1. B5.2E documentation closeout
2. B5.4 Thread Pressure
3. functional Thread Handoff lifecycle
4. independent end-to-end verification in Project, Core and Research
```

Core-only verification is insufficient.

Every required operational workflow must function independently in:

```text
Curvature Project
Curvature Core
Curvature Research
```

Deferred until demanded by real project work:

- B5.3 full structured conversation records;
- B6 expanded Department State Bus;
- unified execution ledger;
- additional control-plane automation.

---

# Thread Pressure Requirement

Thread Pressure is mandatory before the operational release.

Each department must have an independent persisted estimate and visible state:

```text
GREEN
AMBER
RED
```

The estimate must use locally observable data and must never claim knowledge of
ChatGPT's exact context limit.

At minimum it must account for stored conversation volume, sent task packages,
assistant responses and attachment metadata; recommend a Thread Handoff before
continuity becomes unsafe; and reset only after a successful route transition to
a new department conversation.

---

# Exact Next Step

```text
ASSISTANT-001B5.4A — Thread Pressure Foundation
```

Deliver first:

1. inspect current state, transcript and persistence boundaries;
2. define a local pressure model and thresholds;
3. persist pressure independently by `department_id`;
4. expose GREEN / AMBER / RED in all three department panels;
5. add automated tests for independent department state and restart continuity;
6. do not yet claim completion of the full Thread Handoff lifecycle.
