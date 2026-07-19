# CURVATURE CONSOLE — SOURCE OVERVIEW

Status: Active
Version: 1.0.0
Owner: Project Curvature
Repository: `~/curvature-console`
Last Updated: 2026-07-19

---

# Purpose

This is the preferred Curvature Console overview for shared ChatGPT Project
Sources. The `CONSOLE_` namespace prevents collisions with documentation from
the separate `~/Curvature` repository.

# Canonical Reading Order

1. `CONSOLE_HANDOFF.md`
2. `CONSOLE_DECISIONS.md`
3. `CONSOLE_ROADMAP.md`
4. `CONSOLE_CHANGELOG.md`
5. `CONSOLE_PIPELINE.md`
6. `CONSOLE_README.md`

# Repository Boundary

```text
Curvature Console: ~/curvature-console
Project Curvature: ~/Curvature
```

Curvature Console reads Project Curvature context during the MVP but does not
write that repository or execute Git operations in it.

# Active State

```text
Completed: ASSISTANT-001B5.2A — Browser Bridge Foundation
Active:    ASSISTANT-001B5.2B — Automated Send and Receive
```

# Active Architecture

```text
Curvature Console
→ controlled package
→ ordinary logged-in Chrome
→ Playwright over localhost CDP
→ matching official ChatGPT Project
→ automatic response retrieval
→ originating Console department
→ SQLite persistence
```

# Non-Negotiable Rules

- no paid OpenAI API;
- no API key;
- no manual copy-paste product workflow;
- explicit user-triggered sends during the MVP;
- local browser profile and session data;
- strict department routing;
- explicit browser failures;
- test → verify → document → commit → push.
