# CURVATURE CONSOLE — CURRENT STATE

Status: Operational; B5.5F and B5.6A completed and verified
Version: 2.2.0
Owner: Curvature Core
Last Updated: 2026-07-30

# Purpose

This document is the concise source of truth for the current operational state
of Curvature Console.

# Repository Baseline

```text
Repository: ~/curvature-console
Branch: main
Base commit: ec2067eb064f4f2bf3c879b361f8e75c0a39df3b
Push state before closeout: main == origin/main
Working tree: B5.2R implementation and documentation changes pending commit
```

# B5.2R Verification

Automated verification:

```text
111 tests passed
git diff --check passed
```

Live Core verification:

```text
request_id: 930f45e9ba1a41f6a75842fd1e788f32
department_id: core
route: exact persisted Core conversation URL
message marker: confirmed
assistant response: captured
exchange status: success
background browser: normal Chrome inside Xvfb
physical Chrome window: not shown
owned process cleanup: complete
CDP port 9222 released: true
```

# Implemented B5.2R Capabilities

- lightweight normal Task payloads;
- full context reserved for Thread Handoff;
- immutable `request_id`;
- exact `department_id` and persisted conversation URL binding;
- one dedicated Playwright page per exchange;
- confirmation of the current user message through a unique request marker;
- response acceptance only for the matching request and department;
- stale or foreign result rejection;
- normal Chrome on an invisible Xvfb display;
- visible Chrome only for confirmed login or human verification;
- per-panel activity heartbeat, stage and elapsed time;
- timestamped runtime logs under `data/logs/`;
- request, stage, selector, route and traceback diagnostics;
- owned Chrome/Xvfb process-group cleanup;
- verified release of CDP port 9222.

# Department Validation Policy

The implementation is shared by Project, Core and Research.

B5.2R received deep live validation in Core. Automated tests cover shared
department routing and isolation. Separate Project and Research repetition is
not required unless a department-specific defect appears.

# Known Follow-Up

Generated-file capture exists in earlier repository history and persistence
models, but the current rewritten exchange result does not yet return captured
files. The next corrective sprint must restore and generalise download capture
without assuming ZIP format.

# Exact Next Step

Close, commit and push B5.2R.

Then start:

```text
ASSISTANT-001B5.R2D2 — General Generated-File Capture
```

The sprint must support arbitrary generated files such as `.txt`, `.md`,
`.json`, `.csv`, `.pdf`, images, office documents and `.zip`, preserving the
actual filename and extension.


# B5.R2D2 Active Implementation

The current candidate restores generated-file capture on the deterministic
browser bridge.

Files are captured only from links in the newly completed assistant response.
The actual suggested filename and extension are preserved. No `.zip` extension
is forced.

Captured files are stored under:

```text
data/inbox/<department>/
```

with collision-safe suffixes such as `report-2.txt`.

# B5.R2D2 File-Card Diagnostic Candidate

The first live `.txt` test completed the assistant response but captured zero
files because the generated file was not represented by an `a[href]` inside the
assistant text node.

The active candidate now searches the complete assistant conversation turn,
including file cards and download buttons, and records bounded DOM diagnostics
when no file is captured.

# B5.R2D2 Two-Stage Download Candidate

Live diagnostics proved that ChatGPT can render generated files as buttons
rather than direct links. The active candidate first waits for a direct browser
download. If none starts, it treats the click as opening a preview and searches
the visible page for the real Download control.


# B5.R2D2 Citation Interaction Diagnostic

The current candidate is diagnostic only after a non-downloading generated-file
control is clicked. It records bounded before/after DOM evidence and does not
choose or click a second control.


# B5.R2D2 Active-Layer Diagnostic

The previous general page snapshot was dominated by sidebar controls. The active
diagnostic now follows the focused Close control, records its ancestor chain,
selects a bounded blocking-layer candidate and records every visible interactive
control inside that layer. It still performs no inferred follow-up click.


# B5.R2D2 Generated-File Button Activation

Live evidence confirmed a generated-file card rendered as a button with
`aria-label="curvature-download-test.txt"`. A normal Playwright locator click
focused the button but did not emit a browser download event.

The current implementation now tries five bounded activation methods for the
same candidate: locator click, centre-coordinate mouse click, dispatched
pointer/mouse sequence, Enter and Space. Each method is wrapped in its own
download expectation and logged separately.

# B5.R2D2 Existing File-Card Observer

A dedicated observer now captures browser request/response, download, popup,
console, fetch, XHR, object-URL and anchor-click activity around one exact
file-card activation. This is intended to identify the actual delivery channel
before any further production download logic is added.


# B5.R2D2 Fetch-Response Capture

Live TEST-01 proved that ChatGPT generated-file buttons do not emit a native
Playwright download event. The button starts a fetch chain ending in a
successful `/backend-api/estuary/content` response with
`Content-Disposition: attachment`.

The browser bridge now captures that response body and adapts it to the same
save pipeline used for native downloads.

# B5.R2D2 Generated-File Capture — Closed

Status: **LIVE PASS**

Verified on 2026-07-28:

```text
128 automated tests passed
git diff --check passed
Core generated a real curvature-download-test.txt file card
Console activated the exact file card
ChatGPT delivered the file through a fetch response
final endpoint: /backend-api/estuary/content
HTTP status: 200
Content-Disposition: attachment
captured size: 29 bytes
saved path: data/inbox/core/curvature-download-test.txt
saved content: CURVATURE_DOWNLOAD_CAPTURE_OK
exchange result: downloads=1
```

Confirmed delivery model:

```text
assistant file card
→ button activation
→ interpreter/download metadata
→ Estuary attachment fetch
→ response body capture
→ collision-safe department inbox write
```

A native Playwright download event, Blob URL, programmatic anchor click and popup
were not used in the verified flow.

`Coding Citation` is not a generated-file candidate and must not be activated by
the download scanner.

The temporary TEST-01 observer served its diagnostic purpose and is not part of
the production workflow.

# B5.5A — First Contact Foundation

Status: Completed and verified.

This sprint adds the backend-only foundation for supervised
interdepartmental communication:

- immutable structured handoff records;
- strict Project/Core/Research source and target validation;
- stable handoff and request identifiers;
- explicit lifecycle states and allowed transitions;
- complete visible correspondence timelines;
- SQLite persistence and restart continuity;
- participant and status filtering;
- no UI controls and no automatic delivery.

The implementation intentionally stops before browser routing, approval UI,
loop automation or background sends.

# B5.5B — Bridge Controls

Status: Completed and verified.

A dedicated `Bridge Controls` dialog now provides supervised handoff actions:

- create draft;
- edit draft instruction;
- request approval;
- approve without sending;
- reject;
- hold;
- redirect before delivery;
- stop;
- inspect the complete visible timeline.

Approval is represented by the explicit `approved` state. It is deliberately
separate from `sent`; B5.5B performs no browser delivery and no background
automation.

# B5.5C — Engage Controlled Delivery

Status: Completed, committed and verified.

Commit `10dbf6c` added one-shot supervised delivery of an approved handoff:

- only an explicitly approved handoff may be delivered;
- the user confirms the delivery before browser activity begins;
- the exact persisted target department conversation URL is used;
- the handoff identifier is included in the delivered message;
- success records received and answered timeline entries;
- browser failure moves the handoff to held with a visible reason;
- no autonomous loop or background interdepartmental conversation is introduced.

# B5.5F — Bounded Normal Task Context

Status: Completed and verified.

Direct comparison of commit `2d21958` with `10dbf6c` confirmed that
`browser_bridge.py` and `transfer_package.py` were byte-identical. The browser
entry path was not changed by B5.5A–B5.5C.

The normal Task payload grew because the two full authoritative Markdown
documents grew while the builder continued embedding both without a size
boundary. Normal Task context is now bounded at document boundaries. Current
state has priority; additional authoritative documents are omitted when the
12,000-character section budget would be exceeded. Thread Handoff remains the
full-context route.

# B5.6A — Reply Viewer

Status: Completed and user-verified.

Panels show `Reply received` and activate `View Replies (N)`. Full transcripts remain persisted and feed Task context and Thread Pressure. A large resizable viewer shows saved tasks and replies.

# 2026-07-30 Closeout Verification

Verified state before final repository commit:

```text
154 automated tests passed
git diff --check passed
Reply Viewer manually verified by the user
normal task ordering and continuity manually verified
B5.5C remains the committed controlled-delivery baseline
```

The next activity is a fresh repository snapshot and an audit of the remaining
interdepartmental communication scope. No further Console feature is approved by
this closeout.
