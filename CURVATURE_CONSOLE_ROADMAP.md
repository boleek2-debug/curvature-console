# CURVATURE CONSOLE ROADMAP

Status: Active corrective development
Version: 2.1.0
Owner: Project Curvature
Last Updated: 2026-07-26

# Product Constraint

Normal Console operation must not require additional AI spending beyond the
user's ChatGPT Plus subscription.

# Completed Milestones

- ASSISTANT-001B1 — Repository and Application Foundation
- ASSISTANT-001B2 — Three-Panel Desktop Shell
- Per-Department Attachments
- ASSISTANT-001B3 — Workspace Configuration and Context Loading
- ASSISTANT-001B4 — Local State and Restart Persistence
- ASSISTANT-001B5.1 — Task and Thread Handoff Packages
- ASSISTANT-001B5.2A — Browser Bridge Foundation
- ASSISTANT-001B5.2B — Browser Lifecycle and One-Click UX
- ASSISTANT-001B5.2C — Durable URL-Only Routing
- ASSISTANT-001B5.2C5 — Lightweight Task Delivery
- ASSISTANT-001B5.2R — Deterministic Browser Bridge Rewrite
- ASSISTANT-001B5.2E — Package Review and Safe Apply
- ASSISTANT-001B5.4 — Thread Pressure and Thread Handoff
- ASSISTANT-001B5.R2D2 — General Generated-File Capture

# B5.2R Verified Result

```text
111 automated tests passed
git diff --check passed
Core live exchange succeeded
background Chrome ran inside Xvfb
physical Chrome window remained hidden
request marker was confirmed
response returned to Core
owned Chrome/Xvfb process group terminated
CDP port 9222 released=true
```

B5.2R is complete after documentation, commit and push.

# Closed Corrective Sprint

## ASSISTANT-001B5.R2D2 — General Generated-File Capture

Purpose:

Restore generated-file capture on top of the rewritten deterministic bridge and
remove any assumption that a generated file must be a ZIP archive.

Deliver:

- generated-file detection scoped to the active assistant response;
- arbitrary file types and extensions;
- actual filename preservation;
- safe filename sanitisation without forced `.zip`;
- collision-safe storage in the Console Download Inbox;
- request, department and conversation provenance;
- persistent metadata and per-panel visibility;
- explicit download success and failure;
- runtime log coverage;
- automated tests;
- live Core proof using at least one non-ZIP file such as `.txt`.

Package Review remains a separate workflow and accepts only valid deployment
packages. A downloaded `.txt` must remain a `.txt` and must not be treated as a
package.

# Active Next Sprint

## ASSISTANT-001B5.5 — Supervised Interdepartmental Communication

### B5.5A — First Contact Foundation

Backend-only deliverables:

- structured handoff aggregate;
- validated source and target departments;
- request and handoff identifiers;
- explicit lifecycle transition model;
- complete correspondence timeline;
- SQLite persistence and restart continuity;
- automated tests;
- no UI and no automatic sends.

### B5.5B — Bridge Controls

Implemented for validation:

- create and inspect handoff;
- request approval, approve, edit, reject, hold, redirect and stop controls;
- explicit `approved` state separated from `sent`;
- full visible action timeline and restart continuity;
- no background sends.

### B5.5C — Controlled Delivery

Only after B5.5B live verification:

- browser delivery using approved active conversation URLs;
- bounded loop limits;
- optional controlled automation;
- visible stop and failure recovery.


Deliver:

- structured handoff records;
- source and target department;
- full visible correspondence timeline;
- draft, pending approval, sent, received, answered and closed states;
- user controls to approve, edit, reject, hold, redirect or stop;
- request and handoff identifiers;
- safe loop limits;
- optional controlled automation only after the supervised path is verified.

# Maintenance Gate

Every change must preserve:

- strict department isolation;
- exact URL routing;
- immutable request identity;
- invisible normal browser operation;
- visible activity heartbeat;
- runtime diagnostics;
- explicit repository-write approval;
- no automatic commit or push;
- complete automated tests;
- clean Git state.


## B5.R2D2 Candidate Acceptance

Automated validation must cover filename preservation, collision-safe naming,
format-agnostic link detection, request-result transport, persistence and panel
display.

Live acceptance requires Core to generate and return one `.txt` file that is
captured under `data/inbox/core/` without any ZIP conversion.

## B5.R2D2 File-Card Capture Gate

Acceptance now includes generated-file cards rendered outside the assistant text
container. Empty capture must produce actionable bounded DOM diagnostics.

## B5.R2D2 Two-Stage Acceptance

Live acceptance requires a real generated file card to either download directly
or open a preview whose Download control is captured by Console.


# B5.R2D2 Acceptance Result

```text
automated validation: 128 passed
live Core file card: PASS
delivery channel: fetch response
saved file: data/inbox/core/curvature-download-test.txt
exact content verified: CURVATURE_DOWNLOAD_CAPTURE_OK
```
