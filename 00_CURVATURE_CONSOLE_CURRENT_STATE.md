# CURVATURE CONSOLE — CURRENT STATE

Status: Operational
Version: 1.0.0
Owner: Curvature Core
Last Updated: 2026-07-24

# Purpose

This document is the concise source of truth for the current operational state
of Curvature Console.

# Verified Baseline

```text
Repository: ~/curvature-console
Branch: main
Commit: 070eecd
Push: main -> origin/main
Automated tests: 118 passed
git diff --check: passed
Working tree: clean
```

# Operational Status

Curvature Console is operational for normal Project Curvature development.

Completed and verified capabilities:

- simultaneous Project, Core and Research workspaces;
- isolated department roles, drafts, transcripts and attachments;
- dual-repository context loading from `~/curvature-console` and `~/Curvature`;
- durable URL-only ChatGPT conversation routing;
- automated browser send and response capture;
- hybrid browser operation with visible Chrome fallback;
- generated-file capture and persistent Download Inbox;
- Package Review with CREATE / REPLACE / SKIP / CONFLICT classification;
- explicit user-approved Safe Apply;
- path validation, backups, atomic writes and rollback;
- post-apply Git status and diff;
- advisory GREEN / AMBER / RED Thread Pressure;
- pressure-aware handoff controls;
- functional new-chat Thread Handoff;
- persisted new conversation route;
- transcript and pressure reset only after verified handoff completion;
- restart continuity.

# Department Model

The implementation is shared by:

```text
project
core
research
```

Each department remains isolated by immutable `department_id`, persisted route,
context configuration and local state.

Validation policy:

```text
Implement once in shared components.
Perform deep live validation in Core.
Use automated isolation tests for all departments.
Run Project or Research smoke tests when a change is department-specific,
configuration-sensitive or evidence indicates a routing problem.
```

The final B5.4 live validation was completed in Core. Project and Research use
the same implementation and are covered by automated department-isolation
tests. Separate live smoke tests were intentionally waived for this closeout.

# Thread Pressure

Thread Pressure is advisory. Console does not claim access to ChatGPT's exact
remaining context capacity.

Current states:

```text
GREEN — comfortable local headroom
AMBER — prepare a Thread Handoff
RED — start a new chat through Thread Handoff
```

The estimate is independent per department and uses locally observable state.

# Hybrid Browser Model

Normal operation is automated through Playwright and the user's logged-in
ChatGPT Plus browser session.

When browser work is slow or requires observation, ordinary Chrome may become
visible. A long new-chat creation time is not treated as failure while verified
progress continues.

The handoff lifecycle is:

```text
open shared ChatGPT Project
→ enter handoff package
→ submit first message
→ wait for ChatGPT to create a /c/... conversation
→ wait for the completed response
→ persist the new route
→ replace the active transcript
→ recalculate pressure
```

The old route and transcript remain authoritative until the new conversation is
verified.

# Deferred Work

The following are not required before normal Curvature work resumes:

- full structured conversation records;
- expanded Department State Bus;
- unified operation ledger;
- manual ZIP import into Downloads;
- stronger refresh-success notification;
- additional control-plane features.

These items may be promoted when real Curvature work demonstrates a need.

# Exact Next Step

Stop broad Console feature development.

Use Curvature Console for normal work on Project Curvature. Improve Console only
when an operational limitation materially blocks or degrades that work.
