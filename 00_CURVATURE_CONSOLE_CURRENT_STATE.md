# CURVATURE CONSOLE — CURRENT STATE

Status: Active
Last Updated: 2026-07-23
Repository: `~/curvature-console`
Branch: `main`
Current pushed commit: `417f59a Rewrite deterministic ChatGPT browser bridge`

---

# Purpose

This file is the concise current operational state for Curvature Console.

It is a canonical source used both:

- locally by Curvature Console;
- as a copy in the shared ChatGPT Project `Curvature` Sources.

---

# Verified Baseline

```text
61 automated tests passed before the dual-source context change
git diff --check passed
commit 417f59a pushed
main → origin/main
```

The dual-source context implementation currently adds two automated tests,
bringing the local verification target to:

```text
63 automated tests
```

---

# Source Model

Curvature Console uses two distinct authoritative source roots:

```text
console   → ~/curvature-console
curvature → ~/Curvature
```

Console-specific context includes:

- canonical department roles;
- Console handoff;
- Console decisions;
- Console roadmap;
- Console changelog;
- this current-state file.

Project Curvature context includes:

- Project handoff;
- architecture;
- roadmap;
- world and language documentation;
- other department-relevant project documents.

Each document remains authoritative in its own repository.

---

# Browser Bridge State

Implemented and verified for Core:

- immutable request identifiers;
- URL-only department routing;
- exact persisted conversation URL;
- dedicated request page;
- request/response correlation;
- explicit failure on request-page closure;
- no false response persistence;
- draft preservation after failure;
- preservation of unrelated Chrome sessions.

Live Core verification markers:

```text
CORE_BRIDGE_REWRITE_OK
CORE_RESTART_ROUTE_OK
CORE_SECOND_REQUEST_OK
```

---

# Department Rollout State

```text
Core      — dedicated Console-only conversation active and verified
Project   — dedicated Console-only conversation not created yet
Research  — dedicated Console-only conversation not created yet
```

---

# Current Goal

Implement and verify `ASSISTANT-001B5.2D — Generated File Download Capture`.

Required verification:

1. all three workspaces load their canonical Console role;
2. all three workspaces load documents from both named roots;
3. Context Preview reports zero errors;
4. tests and `git diff --check` pass;
5. the change is committed and pushed.

---

# Exact Next Step

1. Verify Core Context Preview.
2. Confirm both `console:` and `curvature:` document labels.
3. Confirm zero load errors.
4. Repeat for Project and Research.
5. Commit and push the dual-source context change.
6. Continue the Core handoff workflow.
7. Create and verify dedicated Project and Research conversations.
8. Resume `ASSISTANT-001B5.2D — Generated File Download Capture` only after all
   three department routes pass live verification.


---

# B5.2D Implementation Candidate

The current package adds:

- generated-file link detection scoped to the new assistant response;
- Playwright download-event capture;
- automatic per-user download inbox creation;
- original filename preservation;
- collision-safe filenames;
- request, department and conversation association;
- SQLite persistence;
- per-department downloaded-file list;
- automated bridge, persistence and UI tests.

Live browser verification is still required before B5.2D is accepted.
