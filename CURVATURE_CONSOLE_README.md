# CURVATURE CONSOLE — SOURCE OVERVIEW

Status: Operational
Last Updated: 2026-07-24

# Purpose

Curvature Console is the local desktop control plane for Project Curvature. It
coordinates three equal departments through the user's existing ChatGPT Plus
session:

```text
Curvature Project
Curvature Core
Curvature Research
```

# Repositories

```text
Curvature Console: ~/curvature-console
Project Curvature: ~/Curvature
```

Console reads both repositories. Reviewed packages may write only to their
declared target repository after explicit user approval. Console never commits
or pushes automatically.

# Verified Release

```text
Commit: 070eecd
Automated tests: 118 passed
git diff --check: passed
main == origin/main
Working tree: clean
```

# Implemented Workflow

- three simultaneous isolated department panels;
- persisted department drafts, transcripts, attachments and routes;
- dual-repository context loading;
- automated ChatGPT browser bridge;
- hybrid visible Chrome fallback;
- generated-file capture;
- persistent Download Inbox;
- Package Review and Safe Apply;
- backups, atomic writes and rollback;
- Git status and diff presentation;
- advisory GREEN / AMBER / RED Thread Pressure;
- pressure-aware new-chat Thread Handoff;
- verified route persistence and pressure reset after handoff;
- restart continuity.

# Operational Policy

Console is complete enough for normal Curvature work. Broad feature development
is paused.

Implement shared functionality once, validate deeply in Core and use automated
department-isolation tests. Run extra Project or Research live tests when a
change is department-specific or evidence indicates a route problem.

# Deferred Until Needed

- structured conversation records;
- expanded Department State Bus;
- unified operation trace;
- manual ZIP import;
- refresh notification and other UX refinements.

# Non-Negotiable Rules

- no mandatory paid OpenAI API;
- no API key;
- no hidden paid operation;
- no routing by conversation title;
- explicit repository-write approval;
- no automatic commit or push;
- preserve the last verified route and transcript on failure;
- test → verify → document → commit → push.

# Exact Next Step

Use Curvature Console for normal Project Curvature development.
