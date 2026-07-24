# CURVATURE CONSOLE — SOURCE OVERVIEW

Status: Active
Last Updated: 2026-07-24

# Purpose

Curvature Console is the local desktop control plane for Project Curvature. It
coordinates three equal departments without using the paid OpenAI API:

```text
Curvature Project
Curvature Core
Curvature Research
```

# Repository Boundary

```text
Curvature Console: ~/curvature-console
Project Curvature: ~/Curvature
```

Console reads both repositories. Reviewed packages may write only to their
declared target repository after explicit user approval. Console never commits
or pushes automatically.

# Current Verified State

```text
Completed: deterministic browser bridge
Completed: dedicated and restart-safe Project/Core/Research routes
Completed: dual-repository context sources
Completed: generated-file capture and persistent Download Inbox
Completed: B5.2E Package Review and Safe Apply
106 automated tests passed
commit 30cbd3c pushed
main == origin/main
working tree clean
```

The verified package workflow is:

```text
ChatGPT generated file
→ Download Inbox
→ Package Review
→ CREATE / REPLACE / SKIP / CONFLICT classification
→ explicit Apply approval
→ re-review
→ backup
→ atomic writes or rollback
→ APPLY_RESULT.json
→ Git status and diff
```

# Operational Release Boundary

Console is sufficiently complete to stop broad feature development. Before main
Project Curvature implementation resumes, the following remain mandatory:

```text
Thread Pressure
→ functional Thread Handoff
→ independent Project/Core/Research verification
→ Console operational release
```

Core-only verification is insufficient. Shared operational functionality must
work independently in all three department panels.

Full structured conversation records, the expanded Department State Bus, the
unified execution ledger and additional control-plane features are deferred
until real Curvature work requires them.

# Active Next Milestone

```text
ASSISTANT-001B5.4A — Thread Pressure Foundation
```

Each department requires an independent persisted GREEN / AMBER / RED estimate.
The estimate must use locally observable data and must not claim exact knowledge
of ChatGPT's context capacity.

# Routing Rule

```text
department_id
→ active_conversation_url
```

Conversation titles, sidebar labels and visual order are never routing keys.

# Non-Negotiable Rules

- no paid OpenAI API;
- no API key;
- no manual copy-paste product workflow;
- explicit user-triggered sends during the MVP;
- local browser profile and session data;
- strict department routing;
- explicit browser failures;
- explicit package approval before repository mutation;
- no automatic commit or push;
- test → verify → document → commit → push.
