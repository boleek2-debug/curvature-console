# ROADMAP

Status: Active  
Version: 0.5.0  
Owner: Project Curvature  
Last Updated: 2026-07-18

---

# Product Constraint

Curvature Console must not require additional AI spending beyond the user's existing ChatGPT Plus subscription.

The current MVP does not use the paid OpenAI API.

Official ChatGPT remains the AI conversation environment.

Curvature Console provides local:

- department workspaces;
- context assembly;
- transfer packages;
- response import;
- persistence;
- attachment manifests;
- future handoffs and state coordination.

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

Completed and verified:

- workspace definitions and roles;
- read-only repository access;
- automatic context loading;
- context preview and refresh.

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

### ASSISTANT-001B5.1 — ChatGPT Transfer Package

Deliver:

- deterministic package schema;
- department identity;
- department role;
- responsibility and authority boundary;
- relevant loaded context;
- bounded local conversation excerpt;
- current draft;
- attachment manifest;
- preview;
- copy to clipboard;
- automated tests.

### ASSISTANT-001B5.2 — Assistant Response Import

Deliver:

- paste/import assistant response;
- explicit target department;
- preview before acceptance;
- append to local department record;
- preserve original text;
- automated tests.

### ASSISTANT-001B5.3 — Department Conversation Records

Deliver:

- structured user and assistant entries;
- timestamps;
- source marker such as `manual-chatgpt-transfer`;
- migration from the existing plain transcript where necessary;
- restart persistence;
- automated tests.

### ASSISTANT-001B5.4 — Attachment Transfer Manifest

Deliver:

- attachment names and paths;
- type and size metadata where available;
- explicit statement that files are not transferred automatically;
- checklist for manual ChatGPT upload;
- department isolation;
- automated tests.

### ASSISTANT-001B5.5 — Workflow Verification and Closeout

Verify:

- Project transfer workflow;
- Core transfer workflow;
- Research transfer workflow;
- state persistence;
- attachment isolation;
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
- browser or desktop integration supported by official interfaces.

A paid provider may only be reconsidered through a new explicit decision that defines:

- purpose;
- optionality;
- default-off behavior;
- spending controls;
- privacy;
- data retention;
- user approval;
- fallback behavior.

It must never silently replace the zero-additional-cost workflow.
