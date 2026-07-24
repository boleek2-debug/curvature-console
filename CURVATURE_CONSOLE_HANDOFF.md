# CURVATURE CONSOLE HANDOFF

Status: Operational
Version: 2.0.0
Owner: Curvature Core
Last Updated: 2026-07-24

# 1. Mission

Curvature Console is the local development control plane for Project Curvature.
It coordinates three equal departments:

- Curvature Project;
- Curvature Core;
- Curvature Research.

It uses the user's existing ChatGPT Plus session and does not require the paid
OpenAI API.

# 2. Repository Boundaries

```text
Console repository: ~/curvature-console
Project repository: ~/Curvature
```

Console may read both repositories. A reviewed package may write only to its
declared target repository after explicit user approval. Console never commits
or pushes automatically.

# 3. Current Verified Repository State

```text
Branch: main
Commit: 070eecd
Automated tests: 118 passed
git diff --check: passed
main == origin/main
Working tree: clean
```

# 4. Completed Operational Workflow

```text
department task
→ bounded transfer package
→ persisted department route
→ Playwright / Chrome send
→ completed response capture
→ originating panel persistence
→ optional generated-file download
→ Package Review
→ explicit Safe Apply
→ backup and atomic write
→ Git status and diff
```

Thread continuity:

```text
local GREEN / AMBER / RED estimate
→ pressure-aware handoff action
→ shared ChatGPT Project
→ new conversation creation
→ verified /c/... route
→ completed first response
→ new route persistence
→ transcript and pressure reset
```

# 5. Live Verification Evidence

Verified during B5.4:

- independent GREEN values displayed in Project, Core and Research;
- Core transitioned live through GREEN, AMBER and RED;
- RED task warning and handoff controls worked;
- a new Core chat was created inside the shared Curvature Project;
- the first handoff response was captured;
- the new Core conversation route was persisted;
- pressure returned to low GREEN;
- restart and `Refresh All Context` preserved an operational state;
- all three context loaders reported zero errors;
- 118 automated tests passed.

# 6. Validation Policy

Shared functionality is implemented once and deeply validated in Core.

Project and Research receive:

- the same `DepartmentPanel`;
- the same browser bridge;
- the same routing and persistence services;
- the same pressure estimator;
- automated department-isolation coverage.

Separate live smoke tests are required only when a change is department-specific,
configuration-sensitive or produces evidence of a route-specific defect.

# 7. Known Non-Blocking Limitations

- new-chat creation may take noticeable time in Chrome/ChatGPT;
- refresh success is visible mainly in the bottom status bar;
- downloaded packages cannot yet be manually imported into the Downloads
  registry from an arbitrary local path;
- Thread Pressure is advisory rather than an exact ChatGPT token reading.

# 8. Deferred Capabilities

- structured conversation records;
- expanded State Bus and formal cross-department handoff records;
- unified operation trace;
- manual package import;
- optional UX refinements.

Do not resume these merely to make Console feel more complete. Promote them only
when actual Curvature work requires them.

# 9. Exact Next Step

Begin normal Project Curvature work through Curvature Console.

The first task should be chosen by Curvature Project. Core implements approved
technical work. Research establishes evidence and confidence where required.

# 10. Engineering Rules

1. Never guess.
2. Inspect current files before uncertain changes.
3. Deliver complete replacement files.
4. Label files as replace, create or leave unchanged.
5. One sprint has one goal.
6. Test and verify before documentation.
7. Document before commit and push.
8. Keep repository state clean.
9. Code and documentation are written in English.
10. Development discussion is conducted in Polish.
11. No hidden paid operation.
