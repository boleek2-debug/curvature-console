# HANDOFF

Status: Active
Version: 0.7.0
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

# 2. Non-Negotiable Cost Decision

Curvature Console must not introduce mandatory AI costs beyond the user's existing ChatGPT Plus subscription.

The approved architecture therefore:

- does not use the paid OpenAI API;
- does not require `OPENAI_API_KEY`;
- does not perform paid provider requests;
- uses official ChatGPT Projects as the AI conversation environment;
- uses local browser automation through ordinary logged-in Chrome;
- connects to Chrome through the Chrome DevTools Protocol;
- keeps the user profile, cookies and session data local;
- uses Curvature Console as the local context, persistence, routing and continuity layer.

Browser automation is an explicitly accepted engineering dependency. It must fail visibly when ChatGPT UI changes, login expires, CAPTCHA appears or Chrome is unavailable.

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

Completed and verified with 22 passing tests.

Commit:

```text
2eec4e6 Implement ASSISTANT-001B4 local state persistence
```

## ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Completed and verified with 32 passing tests.

Commit:

```text
c4e1bd1 Implement B5.1 ChatGPT transfer packages
```

The manual copy-and-paste workflow was subsequently rejected because it added work instead of reducing it. B5.1 package generation remains useful as the controlled payload builder, but its delivery will be automated by the browser bridge.

---

# 4. Verified Browser Automation Proof

The following live proof was completed successfully on Linux:

```text
ordinary Google Chrome
→ persistent local automation profile
→ remote debugging port 9222
→ Playwright CDP connection
→ logged-in ChatGPT Plus session
→ Curvature Core project navigation
→ message-editor detection
→ automatic message entry
→ automatic send
→ assistant-response completion detection
→ exact response extraction
```

Verified response:

```text
CURVATURE_AUTOMATION_OK
```

No manual copy or paste was used in the end-to-end proof.

---

# 5. Active Sprint

## ASSISTANT-001B5.2 — Automated ChatGPT Browser Bridge

Current implementation unit:

```text
ASSISTANT-001B5.2A — Browser Bridge Foundation
```

Goal:

Provide a tested local foundation for launching ordinary Chrome with the dedicated profile, connecting through CDP and mapping Console departments to official ChatGPT Projects.

---

# 6. Exact Next Step

Implement and verify:

- `BrowserBridgeConfig`;
- ordinary Chrome launcher;
- dedicated local browser profile;
- CDP connection lifecycle;
- Project/Core/Research project mapping;
- read-only connection and login probe;
- runtime profile exclusion from Git;
- unit tests without live network access.

After B5.2A:

```text
ASSISTANT-001B5.2B — Automated Send and Receive
```

B5.2B will integrate:

- automatic project navigation;
- package delivery;
- message sending;
- response-start detection;
- response-completion detection;
- exact response extraction;
- department routing;
- SQLite persistence;
- visible timeout and login errors.

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

The profile directory contains private session data and must never be committed.

---

# 8. Department Mapping

```text
project  → Curvature Project
core     → Curvature Core
research → Curvature Research
```

A response must always return to the department that created the task package.

---

# 9. Engineering Rules

1. Never guess.
2. Request current files before modifying uncertain code.
3. Deliver complete replacement files.
4. Label every file as replace, create or leave unchanged.
5. One sprint has one goal.
6. Test → Commit → Push.
7. Update HANDOFF after completed work.
8. Code and documentation are written in English.
9. Development discussion is in Polish.
10. No hidden paid operations.
11. Preserve department authority boundaries.
12. No manual copy-paste workflow as the product path.
13. Browser automation failures must be explicit and recoverable.
