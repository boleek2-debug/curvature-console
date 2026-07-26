# CURVATURE CONSOLE DEVELOPMENT PIPELINE

Status: Active
Version: 1.3.0
Owner: Curvature Core
Last Updated: 2026-07-24

---

# Purpose

This document defines the required development and verification pipeline for Curvature Console.

The pipeline protects:

- repository integrity;
- department boundaries;
- local state;
- browser-session privacy;
- test reliability;
- user control;
- zero-additional-cost operation.

---

# 1. Sprint Rule

One sprint has one explicit goal.

Every implementation unit follows:

```text
inspect current state
→ define exact scope
→ implement complete files
→ automated tests
→ controlled manual verification
→ documentation
→ commit
→ push
→ clean working tree
```

Do not combine unrelated milestones in one commit.

---

# 2. File Rule

Before modifying uncertain code:

- inspect the current files;
- do not reconstruct unseen content from memory;
- provide complete replacement files rather than diffs;
- label each file as:
  - `PODMIEŃ ISTNIEJĄCY`;
  - `DODAJ NOWY`;
  - `NIE RUSZAJ`.

Runtime data and private browser data must never be included in implementation packages or commits.

---

# 3. Documentation Namespace

Canonical Console documents use the `CONSOLE_` prefix. `README.md` remains the
repository landing page. Do not recreate unprefixed Console aliases.

Workspace configuration may continue to reference unprefixed documents from
the main `~/Curvature` repository.

---

# 4. Environment

Verified environment:

```text
Python: 3.11
Qt: PySide6 from Conda Forge
Testing: pytest
Browser automation: Playwright
Browser runtime: /usr/bin/google-chrome-stable
```

Install or refresh the editable package:

```bash
cd ~/curvature-console
conda activate curvature-console
python -m pip install -e .
```

---

# 5. Automated Test Pipeline

Run the full unit suite from the repository root:

```bash
cd ~/curvature-console
conda activate curvature-console
python -m pytest -vv
```

Unit tests must not require:

- a logged-in ChatGPT account;
- live network access;
- an open Chrome instance;
- the user's real browser profile;
- paid API access.

Browser code must be testable through:

- pure configuration tests;
- command construction tests;
- dependency injection;
- mocked Playwright objects;
- deterministic timeout and error tests.

---

# 6. Browser Profile Protection

Dedicated browser profile:

```text
~/curvature-console/data/browser-profile/
```

Requirements:

- excluded by `.gitignore`;
- never copied into downloadable implementation packages;
- never displayed in full diagnostic archives;
- never committed;
- never uploaded as a test fixture;
- never accessed by unit tests.

Before every browser-related commit:

```bash
git status --short
git check-ignore -v data/browser-profile/
```

The profile must be reported as ignored.

---

# 7. Live Browser Verification

Live browser verification is separate from unit tests.

It requires ordinary Chrome started with:

```bash
cd ~/curvature-console

google-chrome-stable \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/curvature-console/data/browser-profile" \
  --no-first-run \
  --no-default-browser-check \
  https://chatgpt.com
```

The user performs login manually.

The expected CDP endpoint is:

```text
http://127.0.0.1:9222
```

Live verification must use a harmless, explicit test task and must not modify Project Curvature repository files.

---

# 8. Browser Lifecycle, One-Click and URL-Routing Verification Matrix

ASSISTANT-001B5.2B must verify all of the following, including cleanup after every terminal outcome.

## Department routing

```text
department_id
→ persisted active_conversation_url
```

Requirements:

- one shared ChatGPT Project;
- no routing by conversation title, sidebar label or visual order;
- accept verified direct and project-scoped conversation URL forms;
- use the shared Project URL only for a new Thread Handoff conversation;
- refuse unknown departments and ambiguous routes.

## Lifecycle

- Playwright stops after success;
- Playwright stops after failure;
- Console-owned headless Chrome terminates after success or failure;
- failed CDP startup terminates the launched process;
- externally owned Chrome is detached but not terminated;
- all send surfaces unlock after success or failure;
- lifecycle stage changes remain visible.

## Send

- correct project selected;
- exactly one visible message editor selected;
- package text entered exactly;
- one explicit click initiated a normal Task send;
- no normal Task confirmation dialog was shown;
- Thread Handoff required exactly one confirmation;
- exactly one message submitted.

## Receive

- baseline assistant-message count captured;
- new assistant response detected;
- response completion detected;
- exact response text extracted;
- timeout produces a visible error;
- incomplete response is not persisted as complete.

## Persistence

- response routed only to the originating department;
- response saved immediately;
- restart preserves the imported response;
- other departments remain unchanged.

## Recovery

- Chrome unavailable;
- CDP endpoint unavailable;
- logged-out session;
- project missing or ambiguous;
- message editor missing or ambiguous;
- CAPTCHA or human verification visible;
- response timeout;
- ChatGPT UI selector change.

Every failure must be explicit. The bridge must not guess.

---

# 9. Manual Verification Sequence

For every department:

```text
1. Start ordinary Chrome with the dedicated profile and CDP.
2. Confirm the user is logged in.
3. Start Curvature Console.
4. Select the department.
5. Create a harmless test task.
6. Trigger automated send.
7. Observe navigation to the mapped ChatGPT Project.
8. Confirm one message was sent.
9. Confirm a completed response was retrieved.
10. Confirm the response appeared only in the originating Console panel.
11. Restart Console.
12. Confirm persistence.
```

Run separately for:

- Curvature Project;
- Curvature Core;
- Curvature Research.

---

# 10. Documentation Gate

Before closing a milestone, update as applicable:

- `CONSOLE_HANDOFF.md`;
- `CONSOLE_ROADMAP.md`;
- `CONSOLE_CHANGELOG.md`;
- `README.md`;
- `CONSOLE_DECISIONS.md`;
- `CONSOLE_PIPELINE.md`.

Documentation must not describe superseded manual copy-paste as the active product workflow.

---

# 11. Commit and Push Gate

Before committing:

```bash
git status --short
python -m pytest -vv
git check-ignore -v data/browser-profile/
```

Then:

```bash
git add <explicit files>
git commit -m "<milestone-specific message>"
git push
git status
```

Required final state:

```text
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

Do not use `git add .` when private runtime files may exist.

---

# 12. Current Exact Next Step

Curvature Console reached operational release at commit:

```text
070eecd
```

Verified baseline:

```text
118 automated tests passed
```

Broad Console development is paused.

Use Console for normal Project Curvature work. Promote a new Console sprint only
when a real operational limitation blocks or materially degrades that work.

Validation policy for shared components:

```text
implement once
→ automated department-isolation coverage
→ deep live validation in Core
→ Project or Research smoke test when department-specific evidence warrants it
```

# 12. Unified Operation Trace

Future cross-module operations must be observable from request to verified
result.

The minimum trace should connect, where applicable:

```text
operation ID
→ department
→ source context
→ browser exchange
→ response
→ generated files
→ package review
→ repository changes
→ tests
→ Git state
→ final status
```

Requirements:

- every transition has an explicit state;
- failures preserve the last verified state;
- file writes are not reported before durable completion;
- UI state must be derived from persisted operation state;
- cleanup must not destroy the only diagnostic evidence of a failed operation;
- no module may silently perform a cross-boundary side effect.

This remains a deferred architectural requirement and must not interrupt the
mandatory B5.4 Thread Pressure and handoff closeout.


# 13. B5.2R Browser Acceptance

A deterministic browser change is not complete until the runtime log proves:

```text
exact persisted route
→ dedicated page
→ editor found
→ current request marker confirmed
→ completed response captured
→ exchange_success
→ owned process-group cleanup
→ CDP port released=true
```

Normal browser execution uses full Chrome inside Xvfb. Visible Chrome is allowed
only for confirmed login or human verification.

The active panel must show a continuously updating activity indicator while the
worker runs.

# 14. Generated-File Acceptance

Generated-file capture must not force ZIP format.

Required live proof:

```text
assistant generates a non-ZIP file
→ Console captures the actual download
→ original filename and extension preserved
→ collision-safe local path
→ request/department/conversation provenance persisted
→ originating panel displays the file
→ record survives restart
```

Package Review is invoked only for a valid deployment package. Ordinary
generated files remain ordinary files.
