# CURVATURE CONSOLE — CURRENT STATE

Status: Operational; CDU-004B7 closed
Version: 3.0.0
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

The next approved implementation area is:

```text
Main Console work-state surface
```

Do not invent a new milestone identifier in this checkpoint. Assign the concrete CDU milestone/substage identifier before implementation begins.

After the work-state surface is operational:

```text
one real Chronicle Console-first end-to-end workflow
→ formal Console-first promotion
→ Tool Adapter Foundation
→ Godot/local build-test integration
→ Research source intake
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

Update the B7 closure documentation, validate the documentation-only diff, commit and push it, create a fresh clean snapshot, then begin the main Console work-state surface milestone.
