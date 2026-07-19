# CURVATURE CONSOLE CHANGELOG

Status: Active
Version: 0.7.1
Owner: Project Curvature
Last Updated: 2026-07-19

---

# Purpose

This document records completed and verified Curvature Console work and accepted architecture decisions.

---

## 2026-07-19

### CONSOLE-DOCS-001 — Documentation Namespace Migration

Completed:

- namespaced canonical Console documents with the `CONSOLE_` prefix;
- preserved standard root `README.md`;
- added `CONSOLE_README.md` for shared ChatGPT Project Sources;
- updated Console cross-document references;
- retained main-repository names in workspace configuration and intentional
  test fixtures.

Result:

Project Curvature and Curvature Console documentation can coexist in one
ChatGPT Project without filename ambiguity.

---

## 2026-07-18

### ASSISTANT-001B5.2A — Browser Bridge Foundation

Completed and verified.

Commit:

```text
a33fa4e Implement B5.2A browser bridge foundation
```

Delivered:

- Playwright dependency declared in `pyproject.toml`;
- `BrowserBridgeConfig`;
- ordinary Google Chrome launcher;
- dedicated local browser-profile path;
- localhost CDP endpoint configuration;
- Playwright CDP connection lifecycle;
- explicit Project/Core/Research mapping;
- read-only connection, login and project probe;
- runtime browser profile excluded from Git;
- unit tests without live ChatGPT dependency;
- updated HANDOFF and ROADMAP architecture.

Department mapping:

```text
project  → Curvature Project
core     → Curvature Core
research → Curvature Research
```

Live proof completed before implementation:

```text
ordinary Chrome
→ persistent local profile
→ CDP connection
→ logged-in ChatGPT Plus
→ Curvature Core navigation
→ automatic message entry
→ automatic send
→ response completion detection
→ exact response extraction
```

Verified assistant response:

```text
CURVATURE_AUTOMATION_OK
```

The complete automated proof required no manual copy or paste.

Result:

Curvature Console now has a tested foundation for automated ChatGPT Plus interaction without the paid OpenAI API.

### Architecture Decision — Automated ChatGPT Browser Bridge

Accepted:

- manual copy-paste is rejected as a product workflow;
- the package builder remains the controlled payload source;
- ordinary logged-in Chrome is controlled locally through CDP;
- Playwright provides browser automation;
- browser profile and session data remain local;
- each response must return to its originating department;
- failures must be explicit for login expiry, CAPTCHA, timeout and UI changes;
- user-triggered automation is required during the MVP.

Recorded in:

```text
CONSOLE_DECISIONS.md — ADR-004
CONSOLE_DECISIONS.md — ADR-005
```

### ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Completed and verified.

Commit:

```text
c4e1bd1 Implement B5.1 ChatGPT transfer packages
```

Delivered:

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
- exact clipboard copy.

Task Package limits:

```text
Long non-role document: 4,000 characters
Recent local conversation: 8,000 characters
```

Thread Handoff Package limits:

```text
Recent local conversation: 24,000 characters
Loaded documents: full content
```

The clipboard delivery UI is superseded as the product path by B5.2 browser automation. The deterministic package builder remains active.

Related Project Curvature documentation commit:

```text
10ed638 Align Console architecture with ChatGPT Plus workflow
```

### Architecture Decision — Zero Additional AI Cost

Accepted:

- Curvature Console must not require AI spending beyond the user's existing ChatGPT Plus subscription;
- the paid OpenAI API is excluded from the default MVP architecture;
- no API key is required;
- no automatic paid provider request is allowed.

The manual workflow portion was later superseded by ADR-004 while the zero-cost rule remained active.

Recorded in:

```text
CONSOLE_DECISIONS.md — ADR-002
```

### ASSISTANT-001B4 — Local State and Conversation Persistence

Completed and verified.

Commit:

```text
2eec4e6 Implement ASSISTANT-001B4 local state persistence
```

### ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed and verified.

Commit:

```text
a934032 Implement ASSISTANT-001B3 workspace context loading
```

### Per-Department Attachments

Completed and verified.

Commit:

```text
8920117 Add per-department attachment queues
```

### ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified.

Commit:

```text
c0085bd Implement ASSISTANT-001B2 three-panel desktop shell
```

### ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified.

Commit:

```text
a6b46f2 Complete ASSISTANT-001B1 application foundation
```

Environment decision:

- PySide6 and Qt are installed through Conda Forge;
- Curvature Console is installed in editable mode;
- Playwright is an explicit Python dependency;
- the approved browser runtime is system Google Chrome controlled through CDP.
