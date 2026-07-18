# ROADMAP

Status: Active
Version: 0.6.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# Product Constraint

Curvature Console must not require additional AI spending beyond the user's existing ChatGPT Plus subscription.

The current MVP:

- does not use the paid OpenAI API;
- does not require an API key;
- uses official ChatGPT Projects;
- uses manual, user-controlled transfers;
- performs no automatic paid request.

See `DECISIONS.md` for the authoritative architecture decision.

---

# Completed Milestones

## ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified.

Commit:

```text
a6b46f2
```

## ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified.

Commit:

```text
c0085bd
```

## Per-Department Attachments

Completed and verified.

Commit:

```text
8920117
```

## ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed and verified.

Commit:

```text
a934032
```

## ASSISTANT-001B4 — Local State and Conversation Persistence

Completed and verified:

- SQLite operational state;
- independent department persistence;
- drafts and conversation text;
- attachment metadata;
- persistent screenshots;
- splitter layout;
- Focus mode;
- restart continuity;
- 22 passing tests.

Commit:

```text
2eec4e6
```

## ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Completed and verified:

- deterministic package schema;
- Task Package;
- Thread Handoff Package;
- department identity;
- department role;
- responsibility and authority boundary;
- mode-specific context;
- bounded local conversation;
- current task;
- attachment manifest;
- preview;
- exact clipboard copy;
- zero network requests;
- zero API dependencies;
- manual Project, Core and Research verification;
- 32 passing tests.

---

# Active Milestone

## ASSISTANT-001B5 — ChatGPT Plus Workflow Integration

Goal:

Enable effective AI-assisted departmental work through the existing ChatGPT Plus subscription without paid API calls.

Scope rule:

```text
Manual, user-controlled transfer through official ChatGPT.
No paid provider dependency.
No automatic network request.
```

### ASSISTANT-001B5.2 — Assistant Response Import

Deliver:

- paste or import assistant response;
- explicit target department;
- preview before acceptance;
- append to local department state;
- preserve original text;
- no network request;
- automated tests.

### ASSISTANT-001B5.3 — Structured Department Conversation Records

Deliver:

- structured user and assistant entries;
- timestamps;
- source markers such as `manual-chatgpt-transfer`;
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
- response import;
- state persistence;
- attachment isolation;
- thread transition in ChatGPT Projects;
- zero network calls;
- zero API dependencies;
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
- cost-rule verification;
- zero-paid-request verification;
- documentation;
- packaging instructions.

---

# Future Optional Work

The following items are not part of the current MVP:

- local inference using user-owned hardware;
- optional local summarisation;
- optional provider abstraction;
- optional paid API integration;
- officially supported browser or desktop integration.

A paid provider may only be reconsidered through a new explicit decision defining:

- purpose;
- optionality;
- default-off behavior;
- spending controls;
- privacy;
- data retention;
- user approval;
- fallback behavior.

It must never silently replace the zero-additional-cost workflow.
