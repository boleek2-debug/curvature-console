# CURVATURE CONSOLE HANDOFF

Status: B5.2R verified; closeout pending
Version: 2.1.0
Owner: Curvature Core
Last Updated: 2026-07-26

# 1. Mission

Curvature Console is the local development control plane for Project Curvature.
It coordinates Curvature Project, Curvature Core and Curvature Research through
the user's existing ChatGPT Plus session without a mandatory paid API.

# 2. Repository Boundaries

```text
Console repository: ~/curvature-console
Project repository: ~/Curvature
```

Console may read both repositories. Repository writes require Package Review
and explicit user approval. Console never commits or pushes automatically.

# 3. Current Repository State

```text
Branch: main
Base commit: ec2067eb064f4f2bf3c879b361f8e75c0a39df3b
B5.2R changes: verified and pending commit
Automated tests: 111 passed
git diff --check: passed
```

# 4. Completed B5.2R Workflow

```text
user-triggered department task
→ lightweight transfer package
→ immutable request_id
→ exact persisted department conversation URL
→ Console-owned Chrome inside invisible Xvfb
→ dedicated Playwright page
→ request-marker confirmation
→ completed assistant response capture
→ request-bound panel persistence
→ dedicated page cleanup
→ Chrome/Xvfb process-group termination
→ CDP port 9222 release verification
```

# 5. Live Evidence

Final Core live proof on 2026-07-26:

```text
Launching normal Chrome on invisible Xvfb display
editor_found selector=#prompt-textarea
user_message_confirmed
exchange_success
owned_process_cleanup_start
owned_process_cleanup_complete cdp_port=9222 released=true
```

The physical desktop remained free of Chrome windows. The Core panel displayed
a continuously updating heartbeat, stage and elapsed time.

# 6. Runtime Diagnostics

Every application run creates:

```text
data/logs/console-YYYYMMDD-HHMMSS.log
```

The log records request identity, department, route, browser ownership mode,
stages, composer diagnostics, message counts, confirmation marker, failures,
tracebacks and cleanup results.

Runtime logs are local artifacts and are not committed.

# 7. Validation Policy

Shared functionality is implemented once and deeply live-validated in Core.

Project and Research use the same bridge, request model, panel implementation
and route persistence. Additional live smoke tests are required only for
department-specific evidence or configuration differences.

# 8. Immediate Closeout

1. Apply the B5.2R closeout documentation.
2. Remove accidental untracked duplicate `CONSOLE_*.md` documents.
3. Keep `data/logs/` untracked.
4. Run `scripts/validate_current.sh`.
5. Stage only the intended implementation, tests, canonical documentation and
   validation script.
6. Commit and push.
7. Confirm `main == origin/main` and a clean working tree except ignored local
   runtime artifacts.

# 9. Next Sprint

```text
ASSISTANT-001B5.R2D2 — General Generated-File Capture
```

Required scope:

- capture generated files from the active assistant response;
- support arbitrary file types rather than ZIP-only assumptions;
- preserve the actual original filename and extension;
- use collision-safe storage;
- bind files to request, department and conversation URL;
- expose the download in the originating panel;
- persist metadata across restart;
- keep Package Review restricted to valid deployment packages.

# 10. Following Sprint

After download capture is stable:

```text
ASSISTANT-001B5.5 — Supervised Interdepartmental Communication
```

Panels may prepare and route structured handoffs, while the user can inspect,
edit, approve, reject, hold or stop every cross-department message.


# 11. B5.R2D2 Implementation Candidate

The active candidate:

- scopes download discovery to the newly completed assistant response;
- supports arbitrary generated file types;
- preserves the browser-suggested filename and extension;
- sanitises unsafe path components;
- uses collision-safe storage under `data/inbox/<department>/`;
- binds captured files to request, department and conversation URL;
- persists metadata and refreshes the originating panel;
- keeps Package Review enabled only for selected `.zip` files.

Required live proof is one generated `.txt` file in Core.

# 12. B5.R2D2 Live Finding

The first live Core test proved that generated-file UI can exist outside the
assistant text node. The next candidate searches the complete assistant turn and
supports links, buttons, role buttons and file-card metadata.

If capture is still empty, the runtime log contains candidate attributes and a
bounded outerHTML excerpt for the exact completed assistant turn.

# 13. Two-Stage File Download

The bridge now supports:

```text
file card click
→ direct download, or
→ preview opens
→ visible Download control discovered
→ browser download captured
```

Preview discovery is logged with bounded candidate attributes and page HTML when
no usable Download control is found.


# 14. Citation Interaction Diagnostic

The prior live run proved only that `Coding Citation` did not emit a direct
browser download and that a later whole-page query saw `Download apps`.

The diagnostic candidate now records generic visible interactive DOM before and
after the click. It does not assume a modal, popover, preview or download
selector.


# 15. Focused Active-Layer Evidence

Confirmed live evidence:

- the body becomes scroll-locked;
- pointer events are disabled on the body;
- focus moves from the composer to `button[data-testid="close-button"]`.

The active diagnostic records the Close button's ancestor chain and every
visible interactive control inside its containing blocking layer. No second
action is performed.


# 16. Generated-File Button Activation

Confirmed live DOM:

```html
<button aria-label="curvature-download-test.txt" type="button">
```

Confirmed prior behaviour: `candidate.click()` changed focus but emitted no
download event.

Current candidate implementation tests deterministic activation methods on the
same file button and does not treat `Coding Citation` as the desired download
source.

# Existing File-Card Observation

Use the already-rendered `curvature-download-test.txt` file card as the test
target. Do not generate a new assistant response for this diagnostic. The
observer records the exact browser channel used by the card.


# Generated-File Delivery Mechanism Confirmed

Confirmed live delivery chain:

```text
file button
→ interpreter/download metadata request
→ estuary/content fetch
→ HTTP 200 attachment response
```

There is no native browser download event, Blob URL, anchor click or popup.
The implementation captures the final attachment response body directly.

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

# Exact Next Step

Close the repository milestone with a clean validation, explicit staging,
commit and push. After that, promote the next approved Console sprint rather
than extending B5.R2D2.
