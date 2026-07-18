# HANDOFF

Status: Active
Version: 0.6.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# 1. Mission

Curvature Console is a standalone internal coordination application for Project Curvature.

It maintains three permanent and equal workspaces:

- Curvature Project
- Curvature Core
- Curvature Research

It is separate from Curvature Platform, World Core, Chronicle Client and gameplay.

Its purpose is to preserve department state, prepare controlled context, support manual ChatGPT Plus workflows and make cross-department work auditable without violating authority boundaries.

---

# 2. Non-Negotiable Cost Decision

Curvature Console must not introduce mandatory AI costs beyond the user's existing ChatGPT Plus subscription.

The default architecture therefore:

- does not use the paid OpenAI API;
- does not require `OPENAI_API_KEY`;
- does not perform automatic model requests;
- does not perform paid background requests;
- does not perform paid web-search or tool calls;
- uses official ChatGPT Projects as the primary AI conversation environment;
- uses Curvature Console as the local context, persistence, transfer and continuity layer.

Any future paid provider integration requires a new explicit Project decision and must remain optional, disabled by default and outside the current MVP.

Authoritative record:

```text
DECISIONS.md — ADR-002
```

---

# 3. Completed Work

## ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified.

Commit:

```text
a6b46f2 Complete ASSISTANT-001B1 application foundation
```

## ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified.

Commit:

```text
c0085bd Implement ASSISTANT-001B2 three-panel desktop shell
```

## Per-Department Attachments

Completed and verified.

Commit:

```text
8920117 Add per-department attachment queues
```

## ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed and verified.

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

## ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Completed and verified:

- deterministic local transfer-package builder;
- compact Task Package;
- comprehensive Thread Handoff Package;
- department identity and authority boundaries;
- full department role inclusion;
- mode-specific context inclusion;
- bounded local conversation;
- current task inclusion;
- attachment manifest;
- package preview;
- exact copy-to-clipboard action;
- explicit zero-network and zero-paid-API markers;
- independent Project, Core and Research package generation;
- manual verification of both modes.

Task Package behavior:

- full role;
- bounded beginning-and-end excerpts for long non-role documents;
- up to 4,000 characters per long non-role document;
- newest 8,000 characters of local conversation.

Thread Handoff Package behavior:

- full loaded context;
- newest 24,000 characters of local conversation;
- explicit continuation instructions for a new chat in the same ChatGPT Project.

Verification:

```text
32 passed
```

Main Project Curvature documentation was aligned with this workflow in:

```text
10ed638 Align Console architecture with ChatGPT Plus workflow
```

---

# 4. Active Sprint

## ASSISTANT-001B5 — ChatGPT Plus Workflow Integration

Current implementation unit:

```text
ASSISTANT-001B5.2 — Assistant Response Import
```

Goal:

Allow a response copied from official ChatGPT to be previewed, accepted and stored in the correct Console department without changing its original text.

---

# 5. Exact Next Step

Implement:

```text
ASSISTANT-001B5.2 — Assistant Response Import
```

Required deliverables:

- explicit target department;
- paste or import action;
- response preview before acceptance;
- preservation of original assistant text;
- append to the selected local department record;
- no automatic network request;
- no paid API dependency;
- automated tests;
- manual verification in Project, Core and Research.

Before implementation, inspect the current state store, department panel, main window and relevant tests.

---

# 6. Approved ChatGPT Projects Workflow

Recommended project structure:

```text
ChatGPT Project: Curvature Project
ChatGPT Project: Curvature Core
ChatGPT Project: Curvature Research
```

Normal task flow:

```text
1. Select a Console department.
2. Refresh or inspect its configured context.
3. Enter the current task.
4. Generate a Task Package.
5. Preview and copy the package.
6. Paste it into the matching official ChatGPT Project chat.
7. Receive the response under the existing Plus subscription.
8. Copy the response.
9. Import it into the same Console department.
10. Persist local state.
```

Thread transition flow:

```text
1. Generate a Thread Handoff Package.
2. Open a new chat in the same department's ChatGPT Project.
3. Paste the handoff.
4. Continue from the confirmed exact next step.
```

The user remains in control of every transfer.

ChatGPT Project memory is useful but is not authoritative project storage.

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
- full cross-department handoff manager;
- local-model integration;
- unsupported browser automation.

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
