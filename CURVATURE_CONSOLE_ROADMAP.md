# CURVATURE CONSOLE ROADMAP

Status: Operational; B5.5D2A candidate ready for commit and live validation
Version: 2.4.0
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
- ASSISTANT-001B5.5D1 — Department-Generated Draft Intake

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
B5.5D1 live end-to-end verification passed
B5.5D1 commit f50e89c pushed
B5.5D1 documentation commit 34bf968 pushed
B5.5D2A candidate: 184 automated tests passed
git diff --check passed
real D2A workflow validation pending
```

# Current Candidate

## ASSISTANT-001B5.5D2A — Supervised Return Path Foundation

Status: Implemented and automated-verified; final live workflow pending.

Delivered candidate:

- `AWAITING_USER_DECISION` after target reply capture;
- `Continue in Target`, `Return to Source`, `Hold`, `Close`;
- explicit review and `Return once`;
- same handoff identity and complete timeline across both directions;
- SQLite migration for new lifecycle states;
- live refresh of the open Hub with selection preservation;
- persistent unread reply highlighting;
- removal of obsolete inline reply receipt;
- no automatic return and no autonomous loop.

Current automated gate:

```text
184 tests passed
git diff --check passed
```

# Exact Next Step

1. Commit and push the B5.5D2A implementation, tests and documentation.
2. Confirm clean `main == origin/main`.
3. Create a fresh timestamped snapshot.
4. Use a real Curvature change for one Project → Core → Project workflow.
5. Close B5.5D2A only after live Hub refresh, unread replies, explicit return,
   same-handoff timeline and no autonomous continuation are verified.

# Following Design Question

After real use, decide whether one long-lived handoff needs explicit update types
such as initial execution plan, progress update, milestone result, blocker and final
closeout. Do not implement the larger hierarchy before observing D2A in real work.
