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
ASSISTANT-001B5.2D2 — General Generated-File Capture
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
