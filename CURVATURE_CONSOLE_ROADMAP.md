# CURVATURE CONSOLE ROADMAP

Status: Active
Version: 1.0.0
Owner: Project Curvature
Last Updated: 2026-07-23

---

# Product Constraint

Curvature Console must not require additional AI spending beyond the user's existing ChatGPT Plus subscription.

The default architecture:

- does not use the paid OpenAI API;
- does not require an API key;
- uses one shared official ChatGPT Project named `Curvature`;
- uses separate department conversations inside that Project;
- automates delivery and response retrieval through a dedicated logged-in Chrome profile;
- performs no hidden paid request;
- requires an explicit user action for every send.

Manual copy-and-paste is not an accepted product workflow.

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

Completed. Commit `2eec4e6`.

## ASSISTANT-001B5.1 — Task and Thread Handoff Packages

Completed. Commit `c4e1bd1`.

The deterministic package builder remains the approved payload source. Clipboard delivery is superseded by browser automation.

## ASSISTANT-001B5.2A — Browser Bridge Foundation

Completed. Commit `a33fa4e`.

Delivered:

- Playwright dependency;
- Chrome/CDP configuration;
- dedicated local browser profile;
- visible live browser proof;
- automatic message entry, send and exact response extraction.

## ASSISTANT-001B5.2B — Browser Lifecycle and One-Click UX

Completed and verified; final closeout commit pending.

Delivered:

- one-click normal Task sending;
- one confirmation only for Thread Handoff;
- explicit browser lifecycle stages;
- recoverable browser errors;
- cleanup of Console-owned browser processes;
- visible fallback after headless failure;
- originating-panel-only UI locking;
- restoration after success or failure.

## ASSISTANT-001B5.2C — Durable URL-Only Conversation Routing

Completed and verified; final closeout commit pending.

Delivered:

- one shared ChatGPT Project model;
- routing by `department_id` and persisted `active_conversation_url`;
- no routing by conversation title, sidebar label or element position;
- history of department conversation URLs;
- support for direct and project-scoped ChatGPT conversation URLs;
- shared Project URL reserved for new Thread Handoff conversations;
- successful live Core verification;
- full automated suite: `56 passed`.

---

# Active Corrective Unit

## ASSISTANT-001B5.2R — Deterministic Browser Bridge Rewrite

Core implementation and live validation completed.

Delivered:

- immutable `request_id`;
- request-bound `department_id`;
- exact persisted conversation URL;
- one dedicated page per request;
- confirmation of the current user message;
- request marker correlation;
- capture of only the newly generated assistant response;
- UI acceptance only when request and department both match;
- explicit failure when the request page closes;
- preservation of the draft after failure;
- no arbitrary existing-tab selection;
- no closure of unrelated browser pages.

Verified on Core:

```text
61 automated tests passed
CORE_BRIDGE_REWRITE_OK
CORE_RESTART_ROUTE_OK
CORE_SECOND_REQUEST_OK
controlled page-close failure passed
```

Rollout policy:

1. Core is the validation department.
2. After documentation, commit, push and full Thread Handoff, normal work moves
   to the dedicated Core conversation through Console.
3. Dedicated Console-only conversations are then created for Project and
   Research.
4. B5.2R closes only after Project and Research pass the same live contract.

## ASSISTANT-001B5.2C5 — Lightweight Task Delivery

Implemented and verified in code.

Normal Task packages contain only:

- request marker;
- department identity;
- concise authority reminder;
- current user task;
- attachment manifest;
- concise response instructions.

They do not resend full role documents, repository documentation or local
conversation history.

Full continuity remains exclusive to Thread Handoff.

# Previous Closeout

Before starting new implementation:

```text
tests
→ git diff check
→ browser-profile ignore check
→ documentation
→ explicit staging
→ commit
→ push
→ clean working tree
```

---

# Current Milestone

## ASSISTANT-001B5.2D — Generated File Download Capture

Completed, verified, committed and pushed.

## ASSISTANT-001B5.2E — Package Review and Safe Apply

Completed across three units:

```text
B5.2E1 — read-only package review foundation
B5.2E2 — Package Review UI and live blocked-package verification
B5.2E3 — explicit safe Apply, backup, rollback and Git report
```

Verified baseline:

```text
106 automated tests passed
git diff --check passed
live CREATE / REPLACE / SKIP apply passed
backup and APPLY_RESULT.json verified
no automatic commit or push
working tree clean
```

## ASSISTANT-001B5.4 — Thread Pressure and Handoff Safety

Mandatory next milestone before Project Curvature implementation resumes.

Deliver in controlled units:

### B5.4A — Thread Pressure Foundation

- local observable-volume model;
- independent persisted state per department;
- GREEN / AMBER / RED status;
- visible indicator in Project, Core and Research;
- restart continuity;
- no claim of exact ChatGPT context capacity.

### B5.4B — Pressure Signals and Handoff Readiness

- account for sent tasks, stored responses, local transcript and attachment metadata;
- AMBER recommendation;
- RED high-visibility warning;
- prepare a complete department-specific Thread Handoff package.

### B5.4C — Functional Thread Handoff Lifecycle

- create or resolve the replacement conversation;
- persist its exact URL for the correct department;
- confirm the handoff response;
- continue normal task delivery on the new route;
- reset pressure only after successful route transition;
- preserve prior route history and diagnostics.

### B5.4D — Three-Department Operational Verification

Run the full workflow independently in:

```text
Curvature Project
Curvature Core
Curvature Research
```

Core-only verification is insufficient. Acceptance requires pressure, handoff,
new-route persistence, continued response and restart continuity in every
department.

## Deferred Until Required

### ASSISTANT-001B5.3 — Structured Department Conversation Records

Deferred. Implement only when real Console use proves that the current persisted
conversation model is insufficient for pressure calculation or traceability.

### ASSISTANT-001B5.5 — Expanded Workflow Closeout

Deferred beyond the operational release except for the three-department tests
required by B5.4D.

# Planned Milestones

## ASSISTANT-001B6 — Department State Bus and Handoffs

- department summaries;
- controlled cross-department awareness;
- explicit handoff creation;
- handoff attachments;
- handoff status transitions;
- authority-boundary enforcement.

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
- officially supported desktop integration if OpenAI exposes one;
- unattended background agents only after a new explicit architecture decision.

A paid provider must never silently replace the ChatGPT Plus browser workflow.


## B5.2D Implementation Verification

Acceptance requires:

- download event belongs to the current request page;
- link belongs to the newly generated assistant response;
- original filename is preserved;
- filename collisions do not overwrite existing files;
- metadata records request, department and conversation;
- downloaded files remain visible after restart;
- unrelated browser pages and downloads are untouched;
- live generated ZIP capture succeeds.


---

# Strategic Control-Plane Direction

Curvature Console is expected to evolve into the central control plane for the
whole Curvature project.

Future architecture should provide a unified execution ledger connecting:

- department requests;
- source context;
- ChatGPT exchanges;
- generated files;
- package review and apply;
- tests;
- repository and Git state;
- final operation outcomes.

This direction is approved for future architecture planning. It must not interrupt
the mandatory B5.4 Thread Pressure and operational handoff closeout.
