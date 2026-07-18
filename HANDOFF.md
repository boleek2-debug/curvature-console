# HANDOFF

Status: Active
Version: 0.3.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# 1. Completed Work

## ASSISTANT-001B1

Completed and verified:

- standalone repository
- dedicated Conda environment
- package foundation
- minimal desktop application
- 2 automated tests

## ASSISTANT-001B2

Completed and verified:

- simultaneous Project, Core and Research panels
- horizontal splitter
- independent conversation and input areas
- resizable panels
- temporary panel focus
- restoration to the three-panel layout
- 6 automated tests
- commit `00885bd`

## Per-Department Attachments

Completed and verified:

- independent attachment queues
- file picker
- drag and drop
- screenshot paste
- remove selected
- clear queue
- file metadata display
- no automatic cross-department sharing
- 11 automated tests
- commit `8920117`

---

# 2. Active Sprint

ASSISTANT-001B3 — Workspace Configuration and Context Loading

Goal:

Give all three workspaces explicit identities and load their assigned Project Curvature documents automatically.

Required deliverables:

- YAML workspace definitions
- Markdown role documents
- read-only repository reader
- context loader
- visible loaded-document list
- context preview
- manual per-workspace refresh
- refresh-all control
- load-error reporting
- automated tests

---

# 3. Exact Next Step

1. Save the B3 context package.
2. Run the complete test suite.
3. Launch the application.
4. Verify that each department displays loaded context.
5. Open each context preview.
6. Confirm missing files appear as errors without crashing.
7. Commit after verification.

Expected test result:

```text
16 passed
```

---

# 4. Current Repository Relationship

Curvature Console repository:

```text
~/curvature-console
```

Project Curvature repository:

```text
~/Curvature
```

Repository access is read-only during the MVP.

Default workspace context:

- Project: CURVATURE, BLUEPRINT, ROADMAP and HANDOFF
- Core: HANDOFF, BLUEPRINT, ROADMAP, PIPELINE and ASSISTANT_ARCHITECTURE
- Research: LANGUAGE, CURVATURE, ROADMAP and HANDOFF

---

# 5. Out of Scope

- AI integration
- SQLite
- conversation persistence
- layout persistence
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
