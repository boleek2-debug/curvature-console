# CURVATURE CONSOLE — SOURCE OVERVIEW

Status: Active
Version: 2.2.0
Owner: Project Curvature
Last Updated: 2026-07-30

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

# Generated Files and Packages

Generated files returned by ChatGPT are captured from the active assistant turn and
stored under `data/inbox/<department>/` with their original file type. Package
Review is separate and accepts only supported deployment ZIPs containing
`CURVATURE_PACKAGE.json`. Repository writes always require explicit user approval.

# Supervised Interdepartmental Communication

Console provides a persisted handoff model and Bridge Controls for Project, Core
and Research. The user may create, edit, approve, reject, hold, redirect, stop and
engage a handoff. Engage performs one confirmed delivery to the target department's
exact active conversation URL. It does not create an autonomous conversation loop.

# Bounded Tasks and Full Handoffs

Normal Task packages use bounded authoritative context at whole-document
boundaries. Thread Handoff remains the full-context continuity mechanism.

# Viewing Replies

Department panels show `Reply received` and `View Replies (N)`. The Reply Viewer
opens the complete saved task and reply history for that department. The underlying
transcript remains persisted and continues to feed Task context, Thread Pressure and
Thread Handoff after restart.

# Verified Closeout State

```text
B5.5A handoff foundation: complete
B5.5B supervised controls: complete
B5.5C one-shot controlled delivery: complete at commit 10dbf6c
B5.5F bounded normal Task context: complete
B5.6A Reply Viewer: complete and user-verified
automated validation: 154 passed
git diff --check: passed
```

# Non-Negotiable Rules

- no mandatory paid OpenAI API;
- no routing by conversation title;
- no arbitrary existing-tab selection;
- explicit request and department binding;
- user approval before repository writes or interdepartmental delivery;
- no autonomous background department loop;
- no automatic commit or push;
- test → verify → document → commit → push.

# Supervised Communication Hub Candidate

B5.5D1 allows Project, Core and Research to prepare structured handoff proposals
for one another. Valid proposals returned in department responses are captured
as persistent drafts in the shared Communication Hub. The user still reviews,
edits, approves and explicitly delivers every handoff; no autonomous
interdepartmental conversation is introduced.
