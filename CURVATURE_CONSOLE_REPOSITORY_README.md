# Curvature Console Repository

Curvature Console is the operational local development control plane for
Project Curvature.

It provides three permanent and equal departmental workspaces:

- Curvature Project;
- Curvature Core;
- Curvature Research.

The application is separate from Curvature Platform, World Core, Chronicle
Client and gameplay.

# Current Release

```text
Status: Operational
Commit: 070eecd
Automated tests: 118 passed
Branch: main
Remote: origin/main
```

# Product Model

One shared official ChatGPT Project named `Curvature` contains successive
department conversations.

```text
department_id
→ persisted active_conversation_url
```

Titles and sidebar order are never routing keys.

Console builds bounded Task or Thread Handoff packages, sends them through the
user's logged-in ChatGPT Plus browser session, captures completed responses and
persists them only in the originating department.

# Implemented Capabilities

## Workspace

- simultaneous three-panel layout;
- Focus mode;
- isolated roles and context;
- independent drafts, transcripts and attachments;
- dual-repository context loading;
- restart persistence.

## Browser Workflow

- Playwright automation;
- dedicated local browser profile;
- deterministic request markers;
- URL-only department routing;
- automated send and response capture;
- visible Chrome fallback and observation;
- explicit lifecycle failures.

## Files and Packages

- generated-file capture;
- persistent Download Inbox;
- collision-safe filenames;
- Package Review;
- CREATE / REPLACE / SKIP / CONFLICT classification;
- traversal and unsafe-entry rejection;
- explicit Apply approval;
- re-review before write;
- backup, atomic writes and rollback;
- `APPLY_RESULT.json`;
- Git status and diff;
- no automatic commit or push.

## Thread Continuity

- advisory per-department Thread Pressure;
- GREEN / AMBER / RED states;
- pressure-aware controls;
- functional new-chat Thread Handoff;
- wait for a real `/c/...` route;
- persist the new route only after verified completion;
- reset transcript and pressure after success;
- preserve the previous verified state after failure.

# Hybrid Browser Model

Automation remains the default. Ordinary Chrome may be shown when browser work
is slow, observable or needs user intervention.

Creating a new ChatGPT conversation can take noticeably longer than sending a
task to an existing conversation. Console waits while verified progress
continues instead of treating ordinary slowness as an immediate failure.

# Environment

```text
Python 3.11
PySide6
PyYAML
pytest
Playwright
Google Chrome Stable
SQLite
```

Create or repair the environment:

```bash
cd ~/curvature-console
conda activate curvature-console
python -m pip install -e .
```

Run:

```bash
python -m curvature_console.main
```

Test:

```bash
python -m pytest -q
```

# Cost Rule

Normal operation uses the existing ChatGPT Plus subscription.

- no mandatory OpenAI API;
- no API key;
- no automatic paid model, tool or search request;
- any future paid integration requires a separate decision and must be optional.

# Repository Safety

Console repository:

```text
~/curvature-console
```

Project repository:

```text
~/Curvature
```

Repository writes require an eligible reviewed package and explicit approval.
Console does not commit or push.

# Development Status

Broad Console feature development is paused. Future features are promoted only
when actual Curvature work demonstrates an operational need.

The exact current state is recorded in:

- `00_CURVATURE_CONSOLE_CURRENT_STATE.md`;
- `CURVATURE_CONSOLE_HANDOFF.md`;
- `CURVATURE_CONSOLE_ROADMAP.md`;
- `CURVATURE_CONSOLE_CHANGELOG.md`;
- `CURVATURE_CONSOLE_DECISIONS.md`;
- `CURVATURE_CONSOLE_PIPELINE.md`.
