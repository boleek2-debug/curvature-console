# HANDOFF

Status: Active
Version: 0.4.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# 1. Completed Work

## ASSISTANT-001B1

Completed and verified.

## ASSISTANT-001B2

Completed and verified:

- simultaneous Project, Core and Research panels
- resizable splitter
- focus and restore
- 6 automated tests
- commit `c0085bd`

## Per-Department Attachments

Completed and verified:

- independent attachment queues
- files, screenshots and drag-and-drop
- 11 automated tests
- commit `8920117`

## ASSISTANT-001B3

Completed and verified:

- YAML workspace definitions
- Markdown roles
- read-only repository reader
- automatic document loading
- context preview
- manual refresh
- 16 automated tests
- commit `a934032`

---

# 2. Active Sprint

ASSISTANT-001B4 — Local State and Conversation Persistence

Goal:

Preserve operational workspace state across application restarts.

Required deliverables:

- SQLite schema
- separate department state
- conversation transcript persistence
- input draft persistence
- attachment metadata persistence
- persistent pasted screenshots
- splitter width persistence
- Focus mode persistence
- restart continuity
- automated tests

---

# 3. Exact Next Step

1. Save the B4 package.
2. Run the complete test suite.
3. Launch the application.
4. Enter different draft text in all three departments.
5. add at least one attachment
6. resize the panels
7. focus one department
8. close the application
9. launch it again
10. verify that all state is restored
11. commit after verification

Expected test result:

```text
22 passed
```

---

# 4. Storage Decision

Operational state is stored in:

```text
~/curvature-console/data/curvature_console.sqlite3
```

Persistent pasted screenshots are stored under:

```text
~/curvature-console/data/attachments/<department>/
```

The SQLite database is local runtime data and remains excluded from Git.

Project Curvature repository access remains read-only.

---

# 5. Out of Scope

- OpenAI integration
- sending messages
- semantic conversation model
- Department State Bus
- handoffs
- repository writes
- Git operations

---

# 6. Engineering Rules

1. Never guess.
2. Request current files before modifying uncertain code.
3. Deliver complete replacement files.
4. Label every file as replace, create or leave unchanged.
5. One sprint has one goal.
6. Test → Commit → Push.
7. Update HANDOFF after completed work.
8. Code and documentation are written in English.
9. Development discussion is in Polish.
