# CURVATURE CONSOLE ARCHITECTURE DECISIONS

Status: Active
Version: 1.3.0
Owner: Project Curvature
Last Updated: 2026-07-23

---

# Purpose

This document records durable Curvature Console architecture and product decisions that must survive sprint changes, handoffs and documentation rewrites.

A decision remains active until it is explicitly superseded by a later decision in this file.

---

# ADR-001 — Separate Internal Console

Status: Accepted
Date: 2026-07-18

## Context

Project Curvature requires persistent coordination between Project, Core and Research without merging their responsibilities into gameplay systems or Curvature Platform.

## Decision

Curvature Console is a separate internal desktop application and repository.

It is not:

- Curvature Platform;
- World Core;
- Chronicle Client;
- gameplay;
- a public player interface.

It provides three permanent and equal workspaces:

- Curvature Project;
- Curvature Core;
- Curvature Research.

## Consequences

- each department preserves independent state;
- authority boundaries are explicit;
- attachments are isolated by department;
- cross-department work requires an explicit handoff;
- Project Curvature repository access remains read-only during the MVP.

---

# ADR-002 — Zero Additional AI Cost

Status: Accepted; workflow section superseded by ADR-004
Date: 2026-07-18

## Context

Direct OpenAI API integration is billed separately from ChatGPT Plus and could create substantial recurring costs under the user's development-message volume, large contexts, code files, documentation and research workload.

The user explicitly decided not to pay more than the existing ChatGPT Plus subscription for normal Curvature Console operation.

## Decision

Curvature Console must not require additional AI spending beyond the user's existing ChatGPT Plus subscription.

The default and MVP architecture therefore:

- does not use the paid OpenAI API;
- does not require an OpenAI API key;
- does not perform paid provider requests;
- does not perform paid background web-search or tool requests;
- does not hide, defer or silently accumulate usage charges;
- uses official ChatGPT Projects as the AI conversation environment.

## Prohibited Default Behavior

Curvature Console must not:

- require billing setup;
- require prepaid API credits;
- ask for `OPENAI_API_KEY` as part of normal installation;
- invoke paid APIs through a Send button;
- perform automatic paid retries;
- perform automatic paid research;
- treat ChatGPT Plus as if it grants API access.

## Superseded Portion

The original manual clipboard transfer workflow and the original prohibition against browser automation are superseded by ADR-004.

The zero-additional-cost rule remains fully active.

## Future Reconsideration

Paid provider integration may be reconsidered only through a new explicit architecture decision.

Such integration must be:

- optional;
- disabled by default;
- separated from the normal Plus workflow;
- protected by visible spending limits;
- protected by explicit user approval;
- documented with current pricing and privacy implications;
- removable without breaking core Console functions.

---

# ADR-003 — Read-Only Project Repository During MVP

Status: Accepted
Date: 2026-07-18

## Context

Curvature Console loads Project Curvature context, but automatic writes would create authority, safety and Git-integrity risks before the handoff system is complete.

## Decision

During the MVP, access to:

```text
~/Curvature
```

remains read-only.

## Consequences

- Console may load configured documents;
- Console may prepare proposed changes;
- Console may not write repository files;
- Console may not execute commits or pushes;
- user-controlled replacement files and Git commands remain the implementation workflow.

---

# ADR-004 — Automated ChatGPT Browser Bridge

Status: Accepted
Date: 2026-07-18
Supersedes: ADR-002 manual-transfer workflow and browser-automation prohibition

## Context

The manual workflow required the user to move repeatedly between Curvature Console and ChatGPT:

```text
Console package
→ copy
→ ChatGPT paste
→ ChatGPT response
→ copy
→ Console paste
```

This added more work than using ChatGPT alone and therefore failed the primary product goal.

The paid OpenAI API remains rejected under ADR-002.

A live proof established that ordinary logged-in Google Chrome can be controlled locally through the Chrome DevTools Protocol and Playwright to:

- open the matching ChatGPT Project;
- locate the message editor;
- enter and send a message;
- detect a completed assistant response;
- extract the exact response text.

## Decision

Curvature Console will automate ChatGPT Plus work through:

```text
Curvature Console
→ ordinary Google Chrome
→ dedicated local browser profile
→ localhost CDP connection
→ Playwright
→ matching official ChatGPT Project
```

Department mapping is fixed:

```text
project  → Curvature Project
core     → Curvature Core
research → Curvature Research
```

The browser bridge must:

- use the user's existing ChatGPT Plus account;
- require no OpenAI API key;
- keep profile and session data local;
- bind each task and response to its originating department;
- expose login expiry, CAPTCHA, timeout and UI-change failures visibly;
- avoid silent retries;
- avoid hidden background paid operations;
- preserve exact assistant response text before any later structuring step.

## Browser Profile Security

The dedicated profile is stored under:

```text
~/curvature-console/data/browser-profile/
```

It contains private cookies and session data.

Therefore:

- it must be excluded from Git;
- credentials must never be embedded in source code;
- the CDP endpoint must bind to localhost;
- the MVP must not expose remote browser control;
- the user performs authentication manually;
- Console may open visible Chrome when login or human verification is required.

## Reliability Rule

Browser automation depends on the official ChatGPT user interface and may break after UI changes.

The bridge must fail explicitly rather than guessing or sending to an uncertain target.

Selectors and completion detection must be covered by automated tests where possible and by controlled live verification before milestone closeout.

## Consequences

Positive:

- no manual copy-paste workflow;
- no additional API billing;
- responses can return directly to the correct Console department;
- the package builder remains the controlled payload source;
- the user retains the official ChatGPT Projects environment.

Trade-offs:

- UI changes may require maintenance;
- login expiry and CAPTCHA require visible user intervention;
- browser automation cannot be treated as an official OpenAI API;
- live browser verification remains necessary;
- unattended background operation is outside the current MVP.

---

# ADR-005 — User-Triggered Automation During MVP

Status: Accepted
Date: 2026-07-18

## Context

Browser automation can interact with the user's live ChatGPT session. Hidden or unattended actions would create routing and safety risks before structured records and recovery controls are complete.

## Decision

During the MVP, every automated send begins from an explicit user action inside Curvature Console.

The Console may automatically:

- launch or connect to the dedicated Chrome profile;
- navigate to the mapped project;
- send the selected package;
- wait for and retrieve the response;
- persist the response.

It must not:

- send tasks on a schedule;
- perform unattended background conversations;
- retry a failed send silently;
- switch departments without explicit task origin;
- continue after login, CAPTCHA or selector uncertainty without user-visible intervention.

## Consequences

- automation removes copy-paste without removing user control;
- live failures remain recoverable;
- background agents may be considered only through a later architecture decision.

---

# ADR-006 — Namespaced Console Documentation

Status: Accepted
Date: 2026-07-19

## Context

Project Curvature and Curvature Console are separate repositories, but their
documents are uploaded to the same ChatGPT Project Sources. Duplicate names
such as `HANDOFF.md` and `ROADMAP.md` made source identity ambiguous.

## Decision

Canonical Console documents use the `CONSOLE_` prefix:

```text
CONSOLE_README.md
CONSOLE_HANDOFF.md
CONSOLE_ROADMAP.md
CONSOLE_CHANGELOG.md
CONSOLE_DECISIONS.md
CONSOLE_PIPELINE.md
```

The repository keeps `README.md` as its conventional landing page.
`CONSOLE_README.md` is preferred for shared Sources.

Workspace configuration and tests that intentionally reference documents from
the main `~/Curvature` repository retain their unprefixed filenames.

## Consequences

- both repositories can coexist in one source collection;
- future Console documents use the `CONSOLE_` namespace;
- old unprefixed Console operational documents are removed rather than kept as
  duplicate aliases.



---

# ADR-007 — One-Click Normal Send and Handoff Confirmation

Status: Accepted
Date: 2026-07-20

## Context

A preview-and-confirm dialog for every normal Task Package added unnecessary work and contradicted the Console goal of being faster than direct browser use.

Starting a new conversation has a larger continuity impact than sending to the active department conversation.

## Decision

- normal Task sending is one explicit click;
- that click builds the current package and starts the browser exchange;
- no additional confirmation is shown for a normal Task;
- Thread Handoff remains a separate action;
- Thread Handoff is the only send action that requires confirmation;
- the confirmation must state that a new ChatGPT conversation will be created and the current one will remain unchanged;
- only one browser exchange may be active at a time;
- every send surface is locked during that exchange and restored after success or failure.

## Consequences

- ordinary work requires fewer UI steps;
- new-thread creation remains deliberate;
- UI lifecycle behavior becomes part of browser-bridge verification.

---

# ADR-008 — Generated Files Require Review Before Repository Apply

Status: Accepted
Date: 2026-07-20

## Context

Automatic download capture can remove manual file transfer, but automatically writing downloaded AI-generated files into a repository would create path, conflict and integrity risks.

## Decision

Generated files must first enter a Console-controlled Download Inbox outside the repository.

Before Apply, Console must provide Package Review that:

- identifies the target repository from explicit package metadata;
- validates every path as repository-relative;
- rejects absolute paths, traversal and escaping symlinks;
- classifies Create, Replace, Conflict and Skip actions;
- shows the complete proposed file list;
- requires explicit user approval;
- backs up replaced files;
- displays a Git diff after application.

Automatic commit and push are excluded until accepted by a later decision.

## Consequences

- download capture and repository writes remain separate trust boundaries;
- AI proposes files, but the user approves application;
- unsafe or ambiguous packages stop before repository mutation.

---

# ADR-009 — One Shared ChatGPT Project and URL-Only Routing

Status: Accepted
Date: 2026-07-20

## Context

The three permanent Console departments are separate conversations inside one shared ChatGPT Project named `Curvature`.

ChatGPT may automatically change conversation titles. Sidebar labels and visual order are presentation details and are not stable routing identifiers.

A live diagnostic observed the project-scoped conversation form:

```text
https://chatgpt.com/g/<project-id>/c/<conversation-id>
```

Direct conversation URLs may also use:

```text
https://chatgpt.com/c/<conversation-id>
```

## Decision

- Curvature Console uses one shared ChatGPT Project;
- every department is identified internally by immutable `department_id`;
- every department stores its current `active_conversation_url` in SQLite;
- routing must never use conversation titles, sidebar text or visible position;
- both verified conversation URL forms are valid;
- the shared Project URL is used only to create a new Thread Handoff conversation;
- after creating a new conversation, Console records the resulting conversation URL as the department's active route;
- unknown or ambiguous routes stop the operation instead of guessing.

## Consequences

- automatic title changes do not break routing;
- department continuity survives UI title changes;
- route history can support recovery and audit;
- ChatGPT web routes remain an observed UI contract rather than an official public API;
- browser changes must produce explicit diagnostics before routing rules are modified.


---

# ADR-010 — Lightweight Normal Task Payload

Status: Accepted
Date: 2026-07-23

## Context

The existing normal Task Package resent the full role, repository documents and
local conversation history during every message. A live browser test showed that
the repeated payload could heavily slow Chrome and cause the editor fill
operation to time out.

All three departments already operate inside persistent conversations in one
shared ChatGPT Project with shared Project Sources.

## Decision

Normal `Send Task` delivery for Project, Core and Research uses a lightweight
payload containing only:

- department identity;
- concise authority boundary;
- current user task;
- attachment manifest;
- concise response instructions.

Normal Task delivery does not resend:

- full role documents;
- repository documentation;
- local conversation history.

The comprehensive context package is reserved for `Send Thread Handoff`.

## Consequences

- normal messages are materially smaller;
- browser entry is faster and less likely to time out;
- repeated context consumption is reduced;
- all three departments use the same lightweight builder path;
- continuity for a new conversation remains explicit through Thread Handoff.


---

# ADR-011 — Dedicated Page and Request-Bound Browser Exchange

Status: Accepted
Date: 2026-07-23

## Context

Live verification showed that a bridge using an arbitrary existing ChatGPT page
could send to the wrong conversation, miss a department request or associate an
unrelated response with a panel.

## Decision

Every browser exchange is immutable and identified by `request_id`.

Each exchange owns:

- one `department_id`;
- one exact persisted conversation URL;
- one dedicated page created for that request;
- one confirmed user message;
- one newly observed assistant response.

The result is accepted by the UI only when both `request_id` and
`department_id` match the pending request.

Existing unrelated ChatGPT pages are never selected for delivery and are never
closed by the bridge.

## Consequences

- arbitrary-tab routing is removed;
- stale or foreign results are ignored;
- a failed user-message confirmation cannot produce a stored assistant result;
- live verification can be performed deterministically by department.


---

# ADR-012 — Dedicated Department Conversations and Hybrid Browser Lifecycle

Status: Accepted
Date: 2026-07-23

## Context

Core live validation showed that deterministic automation requires a conversation
reserved for Console traffic. Mixing manual messages with a request-monitored
conversation can create unrelated new user messages during an exchange.

The browser bridge may connect to an existing Chrome session or launch its own
temporary browser process.

## Decision

Each department uses one dedicated Console-only conversation inside the shared
ChatGPT Project `Curvature`.

Rollout order:

1. Core validates the complete workflow.
2. Core receives a full Thread Handoff and becomes the first operational
   Console-managed department.
3. Project and Research receive dedicated conversations using the same model.
4. Their routes are persisted only after their handoffs are accepted.

Browser ownership rules:

- a dedicated request page is always closed after the exchange;
- a browser session not launched by Console is never closed by Console;
- a browser process launched by Console for an exchange may be closed when that
  Console-owned exchange lifecycle ends;
- login or human-verification recovery may temporarily require visible Chrome;
- ownership, not visibility, determines whether Console may close a browser.

## Consequences

- manual development discussion can remain separate from automated department
  conversations;
- each department route is deterministic;
- unrelated browser sessions remain untouched;
- Console may run with an existing browser or with its own hybrid fallback;
- Thread Handoff is the continuity mechanism when activating a new dedicated
  conversation.


---

# ADR-013 — Dual Repository Context Sources

Status: Accepted
Date: 2026-07-23

## Context

Curvature Console requires two distinct authoritative source sets:

- Console roles, operational state, decisions and implementation roadmap from
  `~/curvature-console`;
- Project Curvature vision, architecture, world, language and project state from
  `~/Curvature`.

A workspace with only one repository root cannot load both sets without unsafe
path traversal or duplicated files.

## Decision

Workspace configuration supports named repository roots.

The canonical source identifiers are:

```text
console   → ~/curvature-console
curvature → ~/Curvature
```

Each configured document explicitly declares its source and repository-relative
path. `RepositoryReader` continues to enforce containment independently inside
each named root.

The canonical `CURVATURE_CONSOLE_*` files are used locally by Console and as
copies uploaded to shared ChatGPT Project Sources.

## Consequences

- Console keeps full awareness of both repositories;
- Console-specific and Project Curvature documents remain distinct;
- no `../` traversal is required;
- source provenance is visible in Context Preview and Thread Handoff;
- each repository retains its own authoritative files.


---

# ADR-014 — Curvature Console as Project Control Plane

Status: Accepted strategic direction
Date: 2026-07-23

## Context

Generated-file capture demonstrated that a visible result may pass through
multiple independent layers:

```text
ChatGPT response
→ rendered UI control
→ browser request
→ local file
→ SQLite record
→ department UI
```

Without one coordinating system, each layer exposes only part of the operation
and failures become difficult to diagnose.

The same problem will recur across repositories, tests, research intake, remote
machines, AI runtimes, asset pipelines and later World Core operations.

## Decision

Curvature Console will evolve into the central control plane for Project
Curvature.

Its role is to:

- coordinate specialised modules;
- preserve department authority;
- observe operation state;
- validate transitions;
- record provenance;
- expose failures;
- provide one trace from request to verified result.

Console does not become the owner of every subsystem's domain truth. It
coordinates systems whose own sources of truth remain authoritative.

A future unified execution ledger should record, where relevant:

```text
operation_id
request_id
department_id
conversation_url
source context
response
generated files
repository target
review decision
applied changes
tests
Git state
final status
failure details
timestamps
```

## Consequences

- observability becomes an architectural requirement rather than optional
  logging;
- modules must expose structured operation state;
- cross-module actions must preserve provenance;
- silent background side effects are rejected;
- Package Apply and later automation should integrate with one operation trace;
- the direction is strategic and must not bypass current milestone sequencing.
