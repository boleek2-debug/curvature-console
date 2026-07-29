# CURVATURE CONSOLE — SOURCE OVERVIEW

Status: Active
Version: 2.1.0
Owner: Project Curvature
Last Updated: 2026-07-26

# Purpose

Curvature Console is the local desktop control plane for Project Curvature. It
coordinates Curvature Project, Curvature Core and Curvature Research through the
user's existing ChatGPT Plus session.

# Repositories

```text
Curvature Console: ~/curvature-console
Project Curvature: ~/Curvature
```

# Current Verified Browser Workflow

```text
department task
→ lightweight package
→ immutable request_id
→ exact persisted conversation URL
→ normal Chrome inside invisible Xvfb
→ dedicated request page
→ confirmed user message marker
→ completed assistant response
→ originating panel
→ process-group cleanup
→ CDP port release
```

Verification:

```text
111 tests passed
git diff --check passed
Core live exchange passed
owned_process_cleanup_complete cdp_port=9222 released=true
```

# Activity and Diagnostics

While an exchange is active, the originating panel displays an indeterminate
progress bar, current stage and elapsed time.

Each application run writes:

```text
data/logs/console-YYYYMMDD-HHMMSS.log
```

Runtime logs are local and must not be committed.

# Browser Policy

Normal automation uses full Chrome inside Xvfb, so no Chrome window appears on
the physical desktop.

Visible Chrome is reserved for confirmed login or human verification.

Console-owned Chrome and Xvfb run in one owned process group and are terminated
after each exchange. Port 9222 is verified as released.

# Download and Package Distinction

Generated-file capture is the next active corrective sprint.

Downloads may be any file type. The original extension must be preserved.

Package Review is separate and applies only to valid deployment packages with a
supported manifest. A normal `.txt`, `.pdf`, image or office document is not a
deployment package.

# Next

```text
ASSISTANT-001B5.R2D2 — General Generated-File Capture
```

Then:

```text
ASSISTANT-001B5.5 — Supervised Interdepartmental Communication
```

# Non-Negotiable Rules

- no mandatory paid OpenAI API;
- no routing by conversation title;
- no arbitrary existing-tab selection;
- explicit request and department binding;
- explicit repository-write approval;
- no automatic commit or push;
- test → verify → document → commit → push.


# Generated-File Inbox

Generated files are stored by department:

```text
data/inbox/project/
data/inbox/core/
data/inbox/research/
```

The file type is preserved. Package Review remains available only for ZIP files
that may contain a supported deployment manifest.

Generated files may be rendered as links, buttons or file cards. Console scans
the complete assistant turn rather than only the text message node.

Generated-file cards may use a two-stage interaction. Console supports both a
direct card download and card → preview → Download.

# Generated Files

Generated files returned by ChatGPT are captured from the active assistant turn
and stored under:

```text
data/inbox/<department>/
```

The verified ChatGPT flow uses an HTTP attachment fetch rather than a native
browser download event. Runtime inbox contents are local and excluded from Git.

# Supervised Handoff Foundation

Curvature Console includes a backend model for visible, restart-safe
interdepartmental handoffs. The current B5.5A implementation provides data,
validation, lifecycle transitions and SQLite persistence only.

There are no B5.5 user controls or automatic department-to-department sends
yet.

# Bridge Controls

Use the toolbar `Bridge Controls` button to create and supervise handoffs.
The dialog stores actions and correspondence in SQLite. It does not send
messages to ChatGPT.
