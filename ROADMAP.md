# ROADMAP

Status: Active
Version: 0.7.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# Product Constraint

Curvature Console must not require additional AI spending beyond the user's existing ChatGPT Plus subscription.

The MVP:

- does not use the paid OpenAI API;
- does not require an API key;
- uses official ChatGPT Projects;
- automates delivery and response retrieval through ordinary logged-in Chrome;
- performs no hidden paid provider request;
- keeps browser profile data local.

Manual copy-and-paste is not an acceptable product workflow.

---

# Completed Milestones

## ASSISTANT-001B1 — Repository and Application Foundation

Completed. Commit `a6b46f2`.

## ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed. Commit `c0085bd`.

## Per-Department Attachments

Completed. Commit `8920117`.

## ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed. Commit `a934032`.

## ASSISTANT-001B4 — Local State and Conversation Persistence

Completed with 22 passing tests. Commit `2eec4e6`.

## ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Completed with 32 passing tests. Commit `c4e1bd1`.

The payload builder remains approved. The manual clipboard delivery workflow is superseded by browser automation.

---

# Active Milestone

## ASSISTANT-001B5 — ChatGPT Plus Browser Integration

Goal:

Enable automated AI-assisted departmental work through the user's existing ChatGPT Plus account without paid API calls.

Architecture:

```text
Curvature Console
→ ordinary Chrome with dedicated local profile
→ Playwright connection over CDP
→ matching official ChatGPT Project
→ automatic task send
→ automatic response retrieval
→ correct Console department
```

### ASSISTANT-001B5.2A — Browser Bridge Foundation

Deliver:

- Playwright dependency;
- Chrome/CDP configuration;
- ordinary Chrome launcher;
- local persistent profile path;
- explicit department-to-project mapping;
- connection lifecycle;
- read-only login and project probe;
- profile data excluded from Git;
- automated unit tests.

### ASSISTANT-001B5.2B — Automated Send and Receive

Deliver:

- navigate to the mapped ChatGPT Project;
- locate the active message editor;
- send a generated Task or Thread Handoff Package;
- detect response creation;
- wait until response stabilises or completion is otherwise detected;
- extract exact assistant response;
- route response to the originating department;
- persist response immediately;
- explicit timeout, login, CAPTCHA and UI-change errors;
- automated tests and manual Project/Core/Research verification.

### ASSISTANT-001B5.3 — Structured Department Conversation Records

Deliver:

- structured user and assistant entries;
- timestamps;
- source markers such as `chatgpt-browser-bridge`;
- migration from existing plain transcript where necessary;
- restart persistence;
- automated tests.

### ASSISTANT-001B5.4 — Thread Pressure Estimation

Deliver:

- local package-size tracking;
- local conversation-size tracking;
- GREEN / AMBER / RED advisory state;
- Thread Handoff recommendation;
- no claim of exact ChatGPT context capacity;
- automated tests.

### ASSISTANT-001B5.5 — Workflow Verification and Closeout

Verify:

- Project workflow;
- Core workflow;
- Research workflow;
- Task Package;
- Thread Handoff Package;
- automated send;
- automated response retrieval;
- state persistence;
- attachment isolation;
- login-expiry recovery;
- zero paid API usage;
- documentation;
- complete test suite.

---

# Planned Milestones

## ASSISTANT-001B6 — Department State Bus and Handoffs

- department summaries;
- controlled cross-department awareness;
- explicit handoff creation;
- handoff attachments;
- handoff status transitions;
- authority-boundary enforcement;
- no automatic sharing of full department conversations.

## ASSISTANT-001B7 — MVP Verification and Closeout

- end-to-end three-department workflow;
- restart continuity;
- authority-boundary verification;
- zero-additional-cost verification;
- browser-recovery verification;
- documentation;
- packaging instructions.

---

# Future Optional Work

- local inference using user-owned hardware;
- optional local summarisation;
- optional provider abstraction;
- optional paid API integration;
- officially supported desktop integration if OpenAI exposes one in the future.

A paid provider may only be reconsidered through a new explicit decision and must never silently replace the ChatGPT Plus browser workflow.
