# HANDOFF

Status: Active
Version: 0.7.1
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

Its purpose is to preserve department state, prepare controlled context and automate work through the user's existing official ChatGPT Projects without requiring the paid OpenAI API.

---

# 2. Active Architecture

The approved architecture:

```text
Curvature Console
→ controlled Task or Thread Handoff Package
→ ordinary logged-in Google Chrome
→ localhost Chrome DevTools Protocol
→ Playwright
→ matching official ChatGPT Project
→ automatic send
→ automatic response retrieval
→ originating Console department
→ SQLite persistence
```

Non-negotiable rules:

- no paid OpenAI API;
- no `OPENAI_API_KEY`;
- no manual copy-paste product workflow;
- no hidden paid operations;
- explicit user-triggered sends during the MVP;
- local browser profile and session data;
- visible failure on login expiry, CAPTCHA, timeout or UI change;
- strict department routing.

Authoritative decisions:

```text
DECISIONS.md — ADR-002
DECISIONS.md — ADR-004
DECISIONS.md — ADR-005
```

---

# 3. Completed Work

## ASSISTANT-001B1 — Repository and Application Foundation

Commit:

```text
a6b46f2 Complete ASSISTANT-001B1 application foundation
```

## ASSISTANT-001B2 — Three-Panel Desktop Shell

Commit:

```text
c0085bd Implement ASSISTANT-001B2 three-panel desktop shell
```

## Per-Department Attachments

Commit:

```text
8920117 Add per-department attachment queues
```

## ASSISTANT-001B3 — Workspace Configuration and Context Loading

Commit:

```text
a934032 Implement ASSISTANT-001B3 workspace context loading
```

## ASSISTANT-001B4 — Local State and Conversation Persistence

Commit:

```text
2eec4e6 Implement ASSISTANT-001B4 local state persistence
```

## ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Commit:

```text
c4e1bd1 Implement B5.1 ChatGPT transfer packages
```

The deterministic package builder remains approved.

The manual clipboard delivery workflow is superseded by browser automation.

## ASSISTANT-001B5.2A — Browser Bridge Foundation

Completed, tested, committed and pushed.

Commit:

```text
a33fa4e Implement B5.2A browser bridge foundation
```

Delivered:

- Playwright dependency;
- Chrome/CDP configuration;
- ordinary Chrome launcher;
- dedicated local browser profile;
- department-to-project mapping;
- CDP connection lifecycle;
- read-only login and project probe;
- browser-profile Git exclusion;
- automated unit tests.

---

# 4. Verified Live Browser Proof

Successfully verified on Linux:

```text
ordinary Google Chrome
→ dedicated local profile
→ remote debugging port 9222
→ Playwright CDP connection
→ logged-in ChatGPT Plus session
→ Curvature Core navigation
→ message-editor detection
→ automatic message entry
→ automatic send
→ response completion detection
→ exact response extraction
```

Verified response:

```text
CURVATURE_AUTOMATION_OK
```

No manual copy or paste was used.

---

# 5. Active Sprint

## ASSISTANT-001B5 — ChatGPT Plus Browser Integration

Current implementation unit:

```text
ASSISTANT-001B5.2B — Automated Send and Receive
```

Goal:

Integrate the proven browser automation into Curvature Console so that a package can be sent from the originating department and the completed assistant response can be retrieved, routed and persisted automatically.

---

# 6. Exact Next Step

Before implementation, inspect:

- `browser_bridge.py`;
- `transfer_package.py`;
- `department_panel.py`;
- `main_window.py`;
- `state_store.py`;
- relevant UI and persistence tests.

Implement:

- navigation to the mapped ChatGPT Project;
- visible-editor selection;
- exact package entry;
- user-triggered send;
- assistant baseline capture;
- new-response detection;
- response-completion detection;
- exact response extraction;
- routing to the originating department;
- immediate SQLite persistence;
- explicit browser/login/CAPTCHA/timeout/UI-change errors;
- unit tests without live ChatGPT;
- live verification for Project, Core and Research.

---

# 7. Browser Runtime

Chrome executable:

```text
/usr/bin/google-chrome-stable
```

Local browser profile:

```text
~/curvature-console/data/browser-profile/
```

CDP endpoint:

```text
http://127.0.0.1:9222
```

The profile contains private session data and must never be committed or included in diagnostics.

Development launch command:

```bash
cd ~/curvature-console

google-chrome-stable \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/curvature-console/data/browser-profile" \
  --no-first-run \
  --no-default-browser-check \
  https://chatgpt.com
```

---

# 8. Department Mapping

```text
project  → Curvature Project
core     → Curvature Core
research → Curvature Research
```

A response must always return to the department that created the package.

Unknown or ambiguous targets must stop the operation.

---

# 9. Storage and Boundaries

Operational state:

```text
~/curvature-console/data/curvature_console.sqlite3
```

Persistent attachments:

```text
~/curvature-console/data/attachments/<department>/
```

Private browser state:

```text
~/curvature-console/data/browser-profile/
```

Project Curvature repository access remains read-only during the MVP.

Console must not execute automatic Git operations.

---

# 10. Engineering Rules

1. Never guess.
2. Request current files before modifying uncertain code.
3. Deliver complete replacement files.
4. Label every file as replace, create or leave unchanged.
5. One sprint has one goal.
6. Test → controlled live verification → documentation → commit → push.
7. Update HANDOFF after completed work.
8. Code and documentation are written in English.
9. Development discussion is in Polish.
10. No hidden paid operations.
11. Preserve department authority boundaries.
12. No manual copy-paste workflow as the product path.
13. Browser automation failures must be explicit and recoverable.
14. Browser profile data must never enter Git.
15. Every automated send requires an explicit user action during the MVP.
