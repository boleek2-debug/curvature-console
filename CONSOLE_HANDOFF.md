# CURVATURE CONSOLE HANDOFF

Status: Active
Version: 0.9.0
Owner: Project Curvature
Last Updated: 2026-07-23

---

# 1. Mission

Curvature Console is a standalone internal coordination application for Project Curvature.

It maintains three permanent and equal workspaces:

- Curvature Project
- Curvature Core
- Curvature Research

The Console preserves department context and local state, sends controlled packages through the user's existing ChatGPT Plus session, retrieves responses, and routes them back to the originating department without using the paid OpenAI API.

---

# 2. Repository and Documentation Boundaries

Curvature Console repository:

```text
~/curvature-console
```

Project Curvature repository:

```text
~/Curvature
```

Canonical Console documents:

```text
CONSOLE_README.md
CONSOLE_HANDOFF.md
CONSOLE_ROADMAP.md
CONSOLE_CHANGELOG.md
CONSOLE_DECISIONS.md
CONSOLE_PIPELINE.md
```

Console currently reads Project Curvature context but does not automatically edit that repository or perform Git operations.

---

# 3. Verified Active Architecture

ChatGPT uses one shared Project:

```text
ChatGPT Project: Curvature
```

The three Console departments use separate conversations inside that shared Project.

Routing never depends on mutable conversation titles, sidebar labels, or visual order.

```text
department_id
→ active_conversation_url stored in SQLite
→ project-scoped ChatGPT conversation
```

The shared Project URL is used only when creating a new conversation:

```text
https://chatgpt.com/g/g-p-6a5ccf24ed988191b1589e5beca5b7c5/project
```

Verified conversation URL forms:

```text
https://chatgpt.com/c/<conversation-id>
https://chatgpt.com/g/<project-id>/c/<conversation-id>
```

Current browser workflow:

```text
one-click Task
→ deterministic Task Package
→ Playwright over localhost CDP
→ dedicated logged-in Chrome profile
→ active department conversation URL
→ automatic send
→ automatic response retrieval
→ originating Console panel
→ SQLite persistence
```

Thread Handoff remains the only send action requiring confirmation.

---

# 4. Completed and Verified Work

Completed foundations:

- ASSISTANT-001B1 — Repository and Application Foundation
- ASSISTANT-001B2 — Three-Panel Desktop Shell
- Per-Department Attachment Queues
- ASSISTANT-001B3 — Workspace Configuration and Context Loading
- ASSISTANT-001B4 — Local State and Conversation Persistence
- ASSISTANT-001B5.1 — Task and Thread Handoff Packages
- ASSISTANT-001B5.2A — Browser Bridge Foundation

Current implementation closeout:

```text
ASSISTANT-001B5.2B — Browser Lifecycle and One-Click UX
ASSISTANT-001B5.2C — Durable URL-Only Conversation Routing
```

Verified:

- normal Task sending requires one click;
- Thread Handoff retains one confirmation;
- only the originating department panel is disabled during its exchange;
- other department panels remain usable;
- browser lifecycle failures return explicit errors instead of leaving the UI stuck;
- headless failure can fall back to visible Chrome;
- response retrieval and local persistence work;
- routing does not use conversation titles;
- project-scoped conversation URLs are accepted;
- a successful live Core exchange returned `PROJECT_SCOPED_ROUTE_OK`;
- full automated suite passed with `56 passed`.

---

# 5. Current Working Tree

Current repository baseline:

```text
branch: main
commit before rewrite: b557ce6eb5556277d0b65114b3f5893c302d78b2
main == origin/main before the uncommitted rewrite
61 automated tests passed
git diff --check passed
```

B5.2C5 lightweight Task delivery is implemented and verified in code:

- normal `Send Task` omits full role documents;
- normal `Send Task` omits repository documentation;
- normal `Send Task` omits local conversation history;
- full continuity remains exclusive to `Send Thread Handoff`.

B5.2R deterministic browser routing is implemented.

Verified Core contract:

```text
one request_id
→ one department_id
→ one persisted Core conversation URL
→ one dedicated request page
→ one confirmed user message
→ one confirmed assistant response
→ one request-bound Core panel result
```

Live Core verification completed:

- dedicated Core conversation created;
- Core route updated in SQLite;
- exact Core route opened;
- request marker persisted in the web conversation;
- `CORE_BRIDGE_REWRITE_OK` returned correctly;
- restart route returned `CORE_RESTART_ROUTE_OK`;
- second request returned `CORE_SECOND_REQUEST_OK`;
- dedicated request tab opened and closed;
- browser pages not owned by Console remained open;
- Console-owned hybrid browser lifecycle completed cleanly;
- manually closing the request page produced an explicit error;
- the interrupted request did not store a false response;
- the task draft remained available after failure.

Project and Research are intentionally not yet activated on the rewritten bridge.
They will receive dedicated Console-only conversations after the Core workflow
handoff is accepted.

B5.2D remains paused until the deterministic bridge is rolled out and verified
for all three departments.

# 6. Exact Next Step

1. Apply this documentation closeout package.
2. Run:
   - complete automated tests;
   - `git diff --check`;
   - `git status --short`.
3. Commit and push the B5.2C5 and B5.2R implementation with current documentation.
4. Generate a full Core Thread Handoff Package.
5. Send the handoff through Console to the dedicated Core conversation.
6. Confirm that dedicated Core understands:
   - the current repository state;
   - the deterministic bridge architecture;
   - the completed Core verification;
   - that Project and Research still require dedicated Console-only conversations;
   - that B5.2D remains paused.
7. Continue normal development through Curvature Console.
8. Create and activate dedicated Project and Research conversations using the
   same verified model.
9. Resume B5.2D only after all three department routes pass live verification.

# 7. Next Sprint Scope

B5.2D must:

- capture files generated by the active ChatGPT response;
- save them to a Console-controlled Download Inbox outside repositories;
- bind every file to its department, exchange and conversation URL;
- preserve safe filenames without silent overwrite;
- report download success and failure visibly;
- remain testable without live ChatGPT.

Repository application is not part of B5.2D.

Safe package review and repository Apply belong to B5.2E.

---

# 8. Runtime Paths

Chrome executable:

```text
/usr/bin/google-chrome-stable
```

Dedicated browser profile:

```text
~/curvature-console/data/browser-profile/
```

CDP endpoint:

```text
http://127.0.0.1:9222
```

SQLite state:

```text
~/curvature-console/data/curvature_console.sqlite3
```

Attachments:

```text
~/curvature-console/data/attachments/<department>/
```

The browser profile contains private session data and must never be committed or included in implementation packages.

---

# 9. Engineering Rules

1. Never guess.
2. Inspect current files before modifying uncertain code.
3. Deliver complete replacement files.
4. Label files as replace, create or leave unchanged.
5. One sprint has one goal.
6. Test → live verification → documentation → commit → push.
7. Route by stable stored URLs, never mutable titles.
8. Keep departments operationally isolated.
9. No hidden paid operations.
10. Browser failures must be explicit and recoverable.
11. Generated files enter an inbox before any repository write.
12. Repository changes require explicit review and approval.
