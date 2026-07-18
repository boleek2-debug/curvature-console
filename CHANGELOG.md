# CHANGELOG

Status: Active
Version: 0.6.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# Purpose

This document records completed and verified Curvature Console work and accepted architecture decisions.

---

## 2026-07-18

### ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Completed and verified:

- deterministic local package builder;
- compact Task Package;
- comprehensive Thread Handoff Package;
- full department role inclusion;
- department identity and authority rules;
- bounded document excerpts for Task Packages;
- full loaded context for Thread Handoff Packages;
- bounded recent local conversation;
- current task inclusion;
- attachment manifest;
- package preview;
- exact clipboard copy;
- explicit zero-network and zero-paid-API markers;
- independent Project, Core and Research package generation.

Task Package limits:

```text
Long non-role document: 4,000 characters
Recent local conversation: 8,000 characters
```

Thread Handoff Package limit:

```text
Recent local conversation: 24,000 characters
Loaded documents: full content
```

Verification:

```text
32 passed
```

Manual verification completed for:

- Project Task Package;
- Project Thread Handoff Package;
- Core Task Package;
- Core Thread Handoff Package;
- Research Task Package;
- Research Thread Handoff Package;
- copy-to-clipboard behavior.

Related Project Curvature documentation commit:

```text
10ed638 Align Console architecture with ChatGPT Plus workflow
```

Result:

Curvature Console now prepares either a compact daily-work package or a comprehensive new-thread continuity package without using a paid API or performing a network request.

### Architecture Decision — Zero Additional AI Cost

Accepted:

- Curvature Console must not require AI spending beyond the user's existing ChatGPT Plus subscription;
- the paid OpenAI API is removed from the default MVP architecture;
- no API key is required;
- no automatic paid model, tool or web-search requests are allowed;
- official ChatGPT Projects remain the primary AI conversation environment;
- Curvature Console is the local context, persistence, transfer and coordination layer.

Recorded in:

```text
DECISIONS.md — ADR-002
```

### ASSISTANT-001B4 — Local State and Conversation Persistence

Completed and verified.

Verification:

```text
22 passed
```

Commit:

```text
2eec4e6 Implement ASSISTANT-001B4 local state persistence
```

### ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed and verified.

Verification:

```text
16 passed
```

Commit:

```text
a934032 Implement ASSISTANT-001B3 workspace context loading
```

### Per-Department Attachments

Completed and verified.

Verification:

```text
11 passed
```

Commit:

```text
8920117 Add per-department attachment queues
```

### ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified.

Verification:

```text
6 passed
```

Commit:

```text
c0085bd Implement ASSISTANT-001B2 three-panel desktop shell
```

### ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified.

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
