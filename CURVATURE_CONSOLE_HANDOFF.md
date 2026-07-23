# CURVATURE CONSOLE HANDOFF

Status: Active
Version: 1.0.0
Owner: Project Curvature
Last Updated: 2026-07-23

---

# 1. Mission

Curvature Console is the internal coordination and control-plane application for
Project Curvature.

It maintains three permanent and equal workspaces:

- Curvature Project;
- Curvature Core;
- Curvature Research.

It preserves context, authority boundaries, browser routing, local state,
responses, attachments and generated files without using the paid OpenAI API.

---

# 2. Repository Boundaries

Curvature Console:

```text
~/curvature-console
```

Project Curvature:

```text
~/Curvature
```

Current rule:

- Console may read both repositories;
- Console-specific files remain authoritative in `~/curvature-console`;
- Project Curvature files remain authoritative in `~/Curvature`;
- B5.2E may apply an explicitly reviewed package only after user approval;
- automatic commit and push remain prohibited.

---

# 3. Canonical Console Documents

```text
00_CURVATURE_CONSOLE_CURRENT_STATE.md
CURVATURE_CONSOLE_HANDOFF.md
CURVATURE_CONSOLE_DECISIONS.md
CURVATURE_CONSOLE_ROADMAP.md
CURVATURE_CONSOLE_CHANGELOG.md
CURVATURE_CONSOLE_README.md
CURVATURE_CONSOLE_PIPELINE.md
CURVATURE_CONSOLE_REPOSITORY_README.md
CURVATURE_CONSOLE_ROLE_CORE.md
CURVATURE_CONSOLE_ROLE_PROJECT.md
CURVATURE_CONSOLE_ROLE_RESEARCH.md
```

The same canonical filenames are used locally and in shared ChatGPT Project
Sources.

---

# 4. Current Verified Repository State

```text
branch: main
commit: 817860e Add generated file download capture
tests: 69 passed
git diff --check: passed
main == origin/main
working tree: clean
```

Previous closeout:

```text
87ec797 Add dual-repository workspace context sources
```

---

# 5. Dual-Source Context State

Named roots:

```text
console   → ~/curvature-console
curvature → ~/Curvature
```

Verified:

```text
Project  — 8 loaded · 0 errors
Core     — 10 loaded · 0 errors
Research — 8 loaded · 0 errors
```

Each loaded document displays `console:` or `curvature:` provenance.

---

# 6. Department Route State

All three departments use dedicated Console-only conversations inside one shared
ChatGPT Project named `Curvature`.

Verified live and after restart:

```text
Core      — operational and restart-safe
Project   — PROJECT_ROUTE_OK
Project   — PROJECT_RESTART_ROUTE_OK
Research  — RESEARCH_ROUTE_OK
Research  — RESEARCH_RESTART_ROUTE_OK
```

Routes are persisted in SQLite and keyed only by immutable `department_id`.

---

# 7. Completed B5.2D

`ASSISTANT-001B5.2D — Generated File Download Capture` is complete, verified,
committed and pushed.

Delivered:

- generated-file detection scoped to the new assistant response;
- support for JavaScript-only download controls;
- authenticated session download;
- Download Inbox outside repositories;
- atomic non-empty file writes;
- original and collision-safe filenames;
- SQLite file records;
- request, department and conversation association;
- per-department UI records;
- restart persistence;
- correct UI refresh;
- conversation restoration after interception.

Inbox:

```text
~/.local/share/curvature-console/download-inbox/
```

Live proof:

```text
core-download-test(7).zip
155 bytes
verification.txt
CORE_DOWNLOAD_CAPTURE_OK
Downloads counter increased
record survived restart
```

---

# 8. Important Implementation Lessons

The ChatGPT-generated file control may:

- appear as a rendered button rather than a normal anchor;
- contain no direct `href`;
- trigger a JavaScript request;
- delegate to Chrome's native Save As workflow if clicked normally.

The accepted implementation therefore captures the generated-file request URL
and retrieves the content through the authenticated browser session rather than
depending on manual Save As.

A successful file must not be registered until:

- HTTP retrieval succeeds;
- response body is non-empty;
- atomic write completes;
- final file size is greater than zero.

---

# 9. Strategic Control-Plane Direction

Curvature Console is expected to become the central project control plane.

Its role is to coordinate and observe specialised systems, not silently absorb
their authority.

Future operations should be traceable across:

```text
request_id
department_id
conversation_url
source documents
assistant response
generated files
package review
repository target
applied files
test results
Git state
final operation status
```

A unified execution ledger is an approved strategic direction for later
architecture work. It must not interrupt the active B5.2E sprint.

---

# 10. Active Milestone

```text
ASSISTANT-001B5.2E — Package Review and Safe Apply
```

Required deliverables:

- machine-readable package manifest;
- target repository identity;
- ZIP-root contract;
- repository-relative path validation;
- absolute-path and traversal rejection;
- unsafe entry and symlink rejection;
- Create / Replace / Conflict / Skip classification;
- complete review before mutation;
- one explicit Apply approval;
- backups for replaced files;
- controlled writes;
- post-apply Git diff;
- no automatic commit or push.

---

# 11. Exact Next Step

1. Take a fresh implementation snapshot only when B5.2E work begins.
2. Inspect current package, state-store and UI boundaries.
3. define and test the manifest schema before repository writes.
4. keep B5.2D Download Inbox immutable as the intake boundary.
5. implement review before apply.
6. stop on every unsafe or ambiguous package condition.
7. test → live verify → document → commit → push.

---

# 12. Engineering Rules

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
