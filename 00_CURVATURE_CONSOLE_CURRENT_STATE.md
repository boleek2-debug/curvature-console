# CURVATURE CONSOLE — CURRENT STATE

Status: B5.2R verified; closeout pending
Version: 1.1.0
Owner: Curvature Core
Last Updated: 2026-07-26

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
ASSISTANT-001B5.2D2 — General Generated-File Capture
```

The sprint must support arbitrary generated files such as `.txt`, `.md`,
`.json`, `.csv`, `.pdf`, images, office documents and `.zip`, preserving the
actual filename and extension.
