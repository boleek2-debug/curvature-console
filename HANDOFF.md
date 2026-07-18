# HANDOFF

Status: Active  
Version: 0.5.0  
Owner: Project Curvature  
Last Updated: 2026-07-18

---

# 1. Mission

Curvature Console is a standalone internal coordination application for Project Curvature.

It maintains three permanent and equal workspaces:

- Curvature Project
- Curvature Core
- Curvature Research

It is not Curvature Platform, World Core, Chronicle Client or gameplay.

Its purpose is to preserve department state, prepare context, support controlled transfers and make cross-department work auditable without violating authority boundaries.

---

# 2. Non-Negotiable Cost Decision

Curvature Console must not introduce mandatory AI costs beyond the user's existing ChatGPT Plus subscription.

The default architecture therefore:

- does not use the paid OpenAI API;
- does not require `OPENAI_API_KEY`;
- does not perform automatic model requests;
- does not perform paid background requests;
- does not perform paid web-search or tool calls;
- uses official ChatGPT as the primary AI conversation interface;
- uses Curvature Console as the local context, persistence and transfer layer.

Any future paid provider integration requires a new explicit project decision and must remain optional, disabled by default and outside the current MVP.

Authoritative record:

```text
DECISIONS.md — ADR-002
```

---

# 3. Completed Work

## ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified:

- standalone repository;
- dedicated Conda environment;
- Python package foundation;
- PySide6 application entry point;
- automated tests.

Commit:

```text
a6b46f2 Complete ASSISTANT-001B1 application foundation
```

## ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified:

- simultaneous Project, Core and Research panels;
- resizable splitter;
- Focus and restore;
- independent department workspaces.

Commit:

```text
c0085bd Implement ASSISTANT-001B2 three-panel desktop shell
```

## Per-Department Attachments

Completed and verified:

- independent attachment queues;
- file selection;
- screenshot paste;
- drag-and-drop;
- no automatic cross-department sharing.

Commit:

```text
8920117 Add per-department attachment queues
```

## ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed and verified:

- YAML workspace definitions;
- Markdown department roles;
- read-only Project Curvature repository reader;
- automatic document loading;
- context preview;
- manual refresh.

Commit:

```text
a934032 Implement ASSISTANT-001B3 workspace context loading
```

## ASSISTANT-001B4 — Local State and Conversation Persistence

Completed and verified:

- SQLite schema;
- separate department state;
- conversation transcript persistence;
- input draft persistence;
- attachment metadata persistence;
- persistent pasted screenshots;
- splitter-width persistence;
- Focus-mode persistence;
- restart continuity;
- corrected Qt splitter persistence test.

Verification:

```text
22 passed
```

Commit:

```text
2eec4e6 Implement ASSISTANT-001B4 local state persistence
```

---

# 4. Active Sprint

## ASSISTANT-001B5 — ChatGPT Plus Workflow Integration

Goal:

Provide a practical AI-assisted workflow through the user's existing ChatGPT Plus subscription without paid API integration.

The Console remains local and prepares controlled transfer packages for manual exchange with official ChatGPT.

### Planned B5 units

1. `ASSISTANT-001B5.1 — ChatGPT Transfer Package`
2. `ASSISTANT-001B5.2 — Assistant Response Import`
3. `ASSISTANT-001B5.3 — Department Conversation Records`
4. `ASSISTANT-001B5.4 — Attachment Transfer Manifest`
5. `ASSISTANT-001B5.5 — Workflow Verification and Closeout`

---

# 5. Exact Next Step

Implement:

```text
ASSISTANT-001B5.1 — ChatGPT Transfer Package
```

Required deliverables:

- department-specific transfer-package builder;
- package preview;
- copy-to-clipboard action;
- role inclusion;
- loaded-context inclusion;
- current draft inclusion;
- bounded local conversation inclusion;
- attachment manifest;
- clear department identity and authority boundary;
- no network request;
- no API dependency;
- no API key;
- automated tests.

Before implementation, inspect the current relevant source files and define the exact transfer-package schema.

---

# 6. Intended Manual Workflow

```text
1. Work in one Curvature Console department.
2. Refresh or inspect its configured context.
3. Enter the current task in the department draft.
4. Generate a ChatGPT transfer package.
5. Preview the package.
6. Copy the package to the clipboard.
7. Paste it into official ChatGPT.
8. Receive the response under the existing Plus subscription.
9. Copy the response.
10. Import or paste it into the same Console department.
11. Persist the updated department state locally.
```

The user remains in control of every transfer.

---

# 7. Storage

Operational state:

```text
~/curvature-console/data/curvature_console.sqlite3
```

Persistent pasted screenshots:

```text
~/curvature-console/data/attachments/<department>/
```

Runtime data remains excluded from Git.

Project Curvature repository access remains read-only during the MVP.

---

# 8. Department Authority

## Curvature Project

Owns:

- direction;
- priorities;
- milestone approval;
- scope decisions;
- arbitration.

## Curvature Core

Owns:

- architecture;
- implementation;
- schemas;
- persistence;
- validation;
- tests.

## Curvature Research

Owns:

- source evaluation;
- evidence;
- hypotheses;
- confidence;
- missing knowledge;
- research graph.

A department may observe concise state from another department, but it must not silently perform another department's work.

Cross-department work requires an explicit handoff.

---

# 9. Out of Scope for B5

- paid OpenAI API integration;
- automatic AI requests;
- automatic paid web search;
- automatic repository writes;
- automatic Git operations;
- Department State Bus implementation;
- full handoff manager;
- local-model integration;
- browser automation that attempts to bypass official ChatGPT controls.

---

# 10. Engineering Rules

1. Never guess.
2. Request current files before modifying uncertain code.
3. Deliver complete replacement files.
4. Label every file as replace, create or leave unchanged.
5. One sprint has one goal.
6. Test → Commit → Push.
7. Update HANDOFF after completed work.
8. Code and documentation are written in English.
9. Development discussion is in Polish.
10. No hidden or automatic paid operations.
11. Preserve department authority boundaries.
