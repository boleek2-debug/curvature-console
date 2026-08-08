# CDU-004B8A — Operator Surface Contract

Status: Approved
Owner: Curvature Console Development Unit
Date: 2026-08-08

## Purpose

Define the minimum operator-facing contract for the new Curvature Console main work-state surface before changing the UI.

The work-state surface must make Curvature easier to operate without removing or hiding functions that are already necessary for real Project, Core, Research and Console Development Unit work.

## Core Principle

The main screen is not a replacement for departmental workspaces.

It is the operator shell above them.

It must answer:

- What is happening now?
- What needs operator attention?
- What is blocked or waiting?
- What has completed?
- What can the operator act on immediately?
- Where can the operator drill down for full departmental detail?

## Required First-Class Areas

### 1. Project — primary operator workspace

Project remains directly usable from the main Console surface.

Required access:

- current Project conversation;
- Project draft/input;
- attachments;
- Send Task;
- current route;
- conversation/thread continuity controls;
- direct drill-down to full Project workspace.

Reason:

Project is the main operator-facing decision workspace for direction, scope, priorities and approvals.

### 2. Thread continuity and context-limit controls

These controls must remain easy to reach and must not be hidden behind deep navigation.

Required access:

- thread pressure / continuity status;
- Task Package;
- Thread Handoff Package;
- current conversation route;
- conversation history / previous routes where supported;
- new-thread continuation workflow.

The new UI must preserve the existing thread-limit recovery workflow.

### 3. Active Work

The main screen must aggregate current operational work across departments.

At minimum show:

- subject/title;
- owning department;
- state;
- whether operator action is required;
- blocker/wait reason when relevant;
- safe drill-down action.

The surface should prefer meaningful work state over raw message history.

### 4. Operator Attention

A dedicated area must show items that need the user's action.

Examples:

- implementation-plan approval;
- scope or consequence decision;
- package ready for review;
- blocker requiring intervention;
- reconcile-before-retry state;
- failed or held operational workflow.

Attention items must be actionable directly or via one clear drill-down.

### 5. Core — implementation output and package control

Core does not receive autonomous repository-write authority.

The main surface must expose when Core has produced implementation output requiring operator action.

Required access:

- current Core task/status;
- generated artifacts/files;
- package ready state;
- validation result where available;
- Package Review;
- Apply / Reject / Request Changes workflow;
- drill-down to full Core workspace.

Safety invariant:

Core may generate changes, but repository application remains a controlled operator action. No silent apply, automatic commit or automatic push.

### 6. Research — source intake and evidence workflow

Research must retain first-class input capability.

Required access:

- Add Sources / Attach Materials;
- source intake queue;
- currently analysing;
- completed;
- needs review / unresolved evidence;
- provenance/confidence issues where relevant;
- drill-down to full Research workspace;
- future Knowledge / Evidence Base entry point.

Research source intake must support the long-term workflow of adding books, papers, PDFs, notes, scans and other source material for structured analysis.

### 7. Department drill-down

Project, Core, Research and Console Development Unit remain separate authority domains.

The main surface may aggregate published status, but must not collapse department context or authority.

Every department must remain reachable for full detail.

### 8. Artifacts and Results

The operator must be able to see newly produced outputs without searching conversations manually.

Examples:

- generated files;
- research results;
- implementation packages;
- validation reports;
- completed handoff results.

### 9. Console Development / System status

CDU and system information should be visible when relevant but need not dominate the main screen.

Required access:

- Console issue/tooling status;
- diagnostics;
- operational failures;
- support/escalation state;
- system/recovery indicators.

## Initial Layout Direction

The first prototype should favour a composition similar to:

```text
+------------------------------------------------------------------+
| CURVATURE CONSOLE                                                |
| Work | Project | Departments | Artifacts | System                |
+--------------------------------+---------------------------------+
| ACTIVE WORK / ATTENTION        | PROJECT                         |
|                                |                                 |
| current work                   | conversation / draft            |
| decisions                      | Send Task                       |
| blockers                       | Attachments                     |
| waiting                        | Thread Pressure                  |
| recent results                 | Thread Handoff                  |
+-------------------------------+----------------------------------+
| CORE                           | RESEARCH                        |
| status                         | source queue                    |
| generated package             | analysis status                 |
| Review Package                | Add Sources                     |
| Open Core                      | Open Research                   |
+-------------------------------+----------------------------------+
| RECENT RESULTS / CDU / SYSTEM                                    |
+------------------------------------------------------------------+
```

This is a prototype direction, not a frozen visual design.

## Non-Goals for B8A

B8A does not:

- redesign the whole application;
- remove the existing three-panel workspace;
- alter department authority;
- add autonomous repository writes;
- add automatic commit/push;
- change Browser Bridge transport semantics;
- replace current handoff or operational-conversation logic;
- finalise visual styling.

## B8 Implementation Sequence

### B8A — Operator Surface Contract

Define what must remain visible, actionable and safe.

### B8B — Read-only Work-State Prototype

Build the first main work-state surface using existing persisted state and existing actions where possible.

No destructive workflow changes.

### B8C — Project and Continuity Integration

Make Project directly usable from the new main surface and expose the existing context-limit / Thread Handoff workflow.

### B8D — Core Output / Package Review Integration

Expose generated Core output, package state and controlled review/apply entry points.

### B8E — Research Source Intake Integration

Expose Research source attachment/intake, queue state and drill-down.

### B8F — Attention / Results / Department Drill-down

Unify decisions, blockers, results and department navigation into the work-state surface.

### B8G — Functional Evaluation

Use the new main surface during normal Curvature work.

Keep the legacy departmental view available.

Accept, adjust or redesign based on real use before promoting the new surface as the default.

## Acceptance Rule

The new work-state surface is successful only if it reduces operator navigation while preserving all critical existing workflows.

If normal use shows that the layout is worse than the legacy view, redesign it. The existing functionality takes priority over the prototype layout.
