# CHANGELOG

Status: Active  
Version: 0.5.0  
Owner: Project Curvature  
Last Updated: 2026-07-18

---

# Purpose

This document records completed and verified Curvature Console work and accepted architecture decisions.

---

## 2026-07-18

### Architecture Decision — Zero Additional AI Cost

Accepted:

- Curvature Console must not require AI spending beyond the user's existing ChatGPT Plus subscription.
- The paid OpenAI API is removed from the default MVP architecture.
- No API key is required.
- No automatic paid model, tool or web-search requests are allowed.
- Official ChatGPT remains the primary AI conversation environment.
- Curvature Console becomes the local context, persistence, transfer and coordination layer.
- ASSISTANT-001B5 is redefined as ChatGPT Plus Workflow Integration.
- The first B5 unit is ChatGPT Transfer Package.

Recorded in:

```text
DECISIONS.md — ADR-002
```

### ASSISTANT-001B4 — Local State and Conversation Persistence

Completed and verified:

- SQLite schema;
- independent Project, Core and Research state;
- conversation text persistence;
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

### ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed and verified:

- YAML workspace definitions;
- Markdown department roles;
- read-only Project Curvature repository reader;
- automatic context loading;
- context preview;
- manual refresh.

Verification:

```text
16 passed
```

Commit:

```text
a934032 Implement ASSISTANT-001B3 workspace context loading
```

### Per-Department Attachments

Completed and verified:

- independent attachment queues;
- file selection;
- screenshot paste;
- drag-and-drop;
- department isolation.

Verification:

```text
11 passed
```

Commit:

```text
8920117 Add per-department attachment queues
```

### ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified:

- simultaneous Project, Core and Research panels;
- resizable splitter;
- Focus mode;
- restoration of all departments.

Verification:

```text
6 passed
```

Commit:

```text
c0085bd Implement ASSISTANT-001B2 three-panel desktop shell
```

### ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified:

- standalone `curvature-console` repository;
- dedicated Conda environment;
- Python package foundation;
- PySide6 application entry point;
- minimal desktop main window;
- reproducible environment definition;
- automated application tests;
- initial README, HANDOFF, ROADMAP and CHANGELOG.

Verification:

```text
2 passed
```

Commit:

```text
a6b46f2 Complete ASSISTANT-001B1 application foundation
```

Environment decision:

- PySide6 and Qt are installed through Conda Forge;
- Curvature Console is installed through pip with `--no-deps`;
- pip-provided PySide6 is not used on the verified Linux environment.
