# CURVATURE CONSOLE — CURRENT STATE

Status: Operational; CDU-004B8A approved
Version: 3.1.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-08

# Purpose

This is the concise operational checkpoint for Curvature Console. Detailed history belongs in `CURVATURE_CONSOLE_CHANGELOG.md`, architecture and policy in the documentation set, and detailed validation evidence in `docs/CONSOLE_TEST_MATRIX.md` and `docs/CONSOLE_STATE_SNAPSHOT.md`.

# Repository Baseline

```text
Repository: ~/curvature-console
Branch: main
Verified commit: 6101810957763035bc71a657e036597ec66697d7
origin/main: same
Working tree at clean B7 checkpoint: clean
```

# Verified Baseline

```text
288 automated tests passed
git diff --check passed
```

Operationally verified foundations include:

- three departmental workspaces and persisted routing;
- Browser Bridge request/response transport;
- generated-file capture;
- package review and safe apply;
- supervised handoffs and return path;
- Console Development Unit diagnostics and escalation;
- durable operational conversations and Operator Review;
- result/blocker/decision attention classification;
- authority/consequence decision gates;
- bounded decision resolution and workflow resume;
- durable Browser Exchange Ledger;
- failure/cancel workflow closure;
- conservative restart reconciliation with no automatic resend.

# CDU-004B7 Closure

CDU-004B7 reliability/recovery hardening is closed.

Recovery rules:

```text
QUEUED / STARTED without durable submission evidence
→ RETRY_PENDING
→ SAFE_RETRY

SUBMITTED / RESPONSE_RECEIVED
or STARTED carrying durable submission evidence
→ RECONCILE_REQUIRED
→ RECONCILE_BEFORE_RETRY

terminal exchange
→ unchanged

startup
→ never automatic resend
```

Repeated reconciliation is idempotent.

Deliberately forcing narrow crash-boundary failures is not a blocking requirement. Normal functional testing continues, and real long-term use acts as a soak test. If a natural interruption occurs, preserve the SQLite state and matching runtime log; any defect must be converted into a deterministic regression test.

# Current Direction

Current milestone:

```text
CDU-004B8 — Main Console Work-State Surface
```

Completed substage:

```text
CDU-004B8A — Operator Surface Contract
```

B8A is approved. It defines the operator-facing contract before UI implementation. The new surface must reduce navigation without removing critical existing workflows.

Next substage:

```text
CDU-004B8B — Read-only Work-State Prototype
```

First-class requirements:

- Project remains directly usable as the primary operator workspace;
- thread-pressure, Task Package and Thread Handoff continuity controls remain easy to reach;
- Active Work and Operator Attention aggregate meaningful state across departments;
- Core generated output remains subject to Package Review and explicit operator Apply/Reject/Request Changes control;
- Research retains first-class source/material intake and future evidence/knowledge-base access;
- departmental authority and full drill-down remain intact;
- artifacts, results, CDU and system diagnostics remain accessible;
- the legacy departmental view remains available while B8 is evaluated in normal use.

The accepted implementation sequence is:

```text
B8A — Operator Surface Contract
B8B — Read-only Work-State Prototype
B8C — Project and Continuity Integration
B8D — Core Output / Package Review Integration
B8E — Research Source Intake Integration
B8F — Attention / Results / Department Drill-down
B8G — Functional Evaluation
```

After B8:

```text
one real Chronicle Console-first end-to-end workflow
→ formal Console-first promotion
→ Tool Adapter Foundation
→ Godot/local build-test integration
→ Research source intake tooling
→ Blender / ComfyUI / controlled image-to-3D pipelines
→ composite workflows
→ Chronicle Beta Feedback Hub
→ voice accessibility
```

Project Value Monitor remains deferred and non-blocking.

# Operational Recovery Evidence

Runtime state:

```text
data/curvature_console.sqlite3
```

Runtime logs:

```text
data/logs/console-YYYYMMDD-HHMMSS.log
```

If a real crash/restart issue appears, preserve both before cleanup.

# Next Step

Begin `CDU-004B8B — Read-only Work-State Prototype`.

Start with reconnaissance of the current `MainWindow` and persisted state sources, then build a non-destructive read-only prototype. Do not remove the legacy departmental view or change repository-write, Browser Bridge, handoff or decision semantics during B8B.
