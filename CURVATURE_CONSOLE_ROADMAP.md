# CURVATURE CONSOLE ROADMAP

Status: Operational; closeout and communication audit
Version: 2.2.0
Owner: Project Curvature
Last Updated: 2026-07-30

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

# Completed Supervised Communication Milestones

## ASSISTANT-001B5.5A — First Contact Foundation

Completed: structured handoff aggregate, explicit lifecycle, complete timeline,
SQLite persistence and restart continuity.

## ASSISTANT-001B5.5B — Bridge Controls

Completed: create, inspect, edit, approval, reject, hold, redirect and stop controls.
Approval remains separate from delivery.

## ASSISTANT-001B5.5C — Engage Controlled Delivery

Completed at commit `10dbf6c`: one approved handoff can be sent once to the target
department after explicit user confirmation. The response is recorded in the
timeline; failure holds the handoff. No autonomous loop exists.

## ASSISTANT-001B5.5F — Bounded Normal Task Context

Completed: normal Tasks use a 12,000-character whole-document authoritative
context budget with Current State priority. Thread Handoff remains full-context.

## ASSISTANT-001B5.6A — Reply Viewer

Completed and user-verified: compact reply receipts, per-department history,
current and earlier reply inspection, and preserved restart/context continuity.

# Current Gate

```text
154 automated tests passed
git diff --check passed
manual Reply Viewer verification passed
manual department ordering verification passed
```

# Exact Next Step

1. Apply the closeout documentation package.
2. Run the full validation script and `git diff --check`.
3. Stage intended files explicitly, commit and push.
4. Confirm `main == origin/main` and a clean working tree.
5. Create a fresh current snapshot.
6. Audit the implemented handoff path against the intended supervised
   Project → Core → Research workflow.
7. Define the smallest remaining communication sprint from evidence in that
   snapshot.

No additional Console feature is approved before the snapshot audit.

# Maintenance Gate

Every change must preserve:

- strict department isolation;
- exact URL routing;
- immutable request identity;
- invisible normal browser operation;
- visible activity heartbeat;
- runtime diagnostics;
- explicit repository-write and delivery approval;
- no autonomous background loop;
- no automatic commit or push;
- complete automated tests;
- clean Git state.

# Active Sprint

## ASSISTANT-001B5.5D1 — Department-Generated Draft Intake

Purpose:

Turn the existing Bridge Controls list into the common supervised intake queue
for all six interdepartmental directions:

```text
Project  → Core
Project  → Research
Core     → Project
Core     → Research
Research → Project
Research → Core
```

Deliver in this increment:

- a strict machine-readable handoff proposal envelope;
- proposal instructions in every department transfer package;
- parsing and validation of proposals returned in assistant responses;
- automatic persistence as reviewable `DRAFT` handoffs;
- duplicate-safe intake for one browser response;
- shared Communication Hub wording and list visibility;
- no automatic approval, delivery, return path or conversation loop.

Following increments remain separate:

- user decision inbox and clearer status grouping;
- supervised response review and return path;
- multi-step correspondence under explicit approval at every boundary.
