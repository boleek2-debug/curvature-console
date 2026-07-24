# CURVATURE CONSOLE HANDOFF

Status: Active
Version: 1.1.0
Owner: Project Curvature
Last Updated: 2026-07-24

---

# 1. Mission

Curvature Console is the internal coordination and control-plane application for
Project Curvature. It maintains three permanent and equal workspaces:

- Curvature Project;
- Curvature Core;
- Curvature Research.

It preserves context, authority boundaries, browser routing, local state,
responses, attachments and generated files without using the paid OpenAI API.

---

# 2. Repository Boundaries

```text
Curvature Console: ~/curvature-console
Project Curvature: ~/Curvature
```

Console may read both repositories. An explicitly reviewed package may write to
its declared target repository only after one user approval. Automatic commit
and push remain prohibited.

---

# 3. Current Verified Repository State

```text
branch: main
commit: 30cbd3cdef56f4141fe3dbc916592ffe82fefe2d
tests: 106 passed
git diff --check: passed
main == origin/main
working tree: clean
```

---

# 4. Verified Department State

Named context roots:

```text
console   → ~/curvature-console
curvature → ~/Curvature
```

Context loading:

```text
Project  — 8 loaded · 0 errors
Core     — 10 loaded · 0 errors
Research — 8 loaded · 0 errors
```

Project, Core and Research each have a dedicated persisted conversation route.
All three routes and restart continuity have passed live verification.

---

# 5. Completed Package Workflow

`ASSISTANT-001B5.2E — Package Review and Safe Apply` is complete.

Delivered across E1, E2 and E3:

- root `CURVATURE_PACKAGE.json` contract;
- repository identity validation;
- ZIP-entry, traversal, absolute-path and symlink protection;
- CREATE / REPLACE / SKIP / CONFLICT classification;
- read-only Package Review UI;
- Apply disabled for blocked packages;
- one explicit Apply approval;
- mandatory re-review immediately before writes;
- stale package and stale repository rejection;
- backups outside repositories;
- atomic writes;
- rollback of created and replaced files on failure;
- `APPLY_RESULT.json`;
- post-apply Git status and diff;
- no automatic commit or push.

Live E3 proof completed with CREATE, REPLACE and SKIP. Backup and metadata were
verified, test changes were restored, and the complete suite passed with 106
tests.

---

# 6. Operational Release Decision

Console development is now restricted to the minimum required for safe daily
Project Curvature work.

Mandatory before returning to the main Curvature implementation roadmap:

```text
B5.2E documentation closeout
→ B5.4 Thread Pressure
→ complete Thread Handoff lifecycle
→ independent Project/Core/Research verification
→ Console operational release
```

Core-only verification is not acceptance evidence for shared functionality.
Every required workflow must pass independently in all three departments.

Deferred until actual project use requires them:

- B5.3 full structured department conversation records;
- B6 expanded Department State Bus and cross-department handoffs;
- unified execution ledger;
- optional control-plane features.

---

# 7. Active Milestone

```text
ASSISTANT-001B5.4A — Thread Pressure Foundation
```

Required first delivery:

- locally derived pressure estimate;
- independent state per `department_id`;
- persisted GREEN / AMBER / RED state;
- visible indicator in Project, Core and Research;
- restart continuity;
- tests proving isolation between departments;
- no assertion of an exact ChatGPT context-window value.

The later B5.4 units must connect AMBER and RED to a functional Thread Handoff,
persist the replacement conversation URL, verify continued messaging on the new
route, and reset pressure only after successful handoff completion.

---

# 8. Required Final Verification Matrix

The operational release requires three independent live passes:

```text
Project  → pressure → handoff → new route → continued response
Core     → pressure → handoff → new route → continued response
Research → pressure → handoff → new route → continued response
```

Each pass must also preserve department-specific attachments, downloads,
context, local state and restart continuity.

---

# 9. Engineering Rules

1. Never guess.
2. Request current files when uncertain.
3. Deliver complete replacement files.
4. Label every file action.
5. One sprint has one goal.
6. Verify displayed state.
7. Test before commit.
8. Commit before push.
9. Keep documentation current.
10. Use English for code and documentation.
11. Use Polish for development discussion.
12. Do not create hidden paid operations.
