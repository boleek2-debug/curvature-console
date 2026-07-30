# CURVATURE CONSOLE ARCHITECTURE DECISIONS

Status: Active
Version: 1.5.0
Owner: Project Curvature
Last Updated: 2026-07-30

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

---

# ADR-015 — Operational Release Requires Thread Pressure and Three-Department Verification

Status: Accepted
Date: 2026-07-24

## Context

The package review and safe-apply workflow is complete. Continuing every planned
Console control-plane feature before returning to Project Curvature would delay
the project without improving the immediate operational path. Thread exhaustion
and incomplete handoff continuity remain the material risks.

## Decision

Curvature Console reaches its first operational release when all of the following
are true:

- B5.2E is documented and closed;
- Thread Pressure provides an independent persisted GREEN / AMBER / RED estimate
  for Project, Core and Research;
- Thread Handoff creates or resolves a replacement conversation, persists its
  route, confirms continuity and resets pressure only after success;
- the complete workflow passes independently in Project, Core and Research.

Core-only verification is explicitly insufficient.

The pressure model is advisory and based only on locally observable data. It must
not claim knowledge of ChatGPT's exact context capacity.

B5.3 structured conversation records, B6 expanded State Bus, the unified
execution ledger and other control-plane features are deferred until actual
Project Curvature work requires them.

## Consequences

- Console work now has a narrow completion boundary.
- Thread Pressure and functional handoff are release requirements, not optional
  enhancements.
- every shared operational feature must be verified in all three departments.
- Project Curvature implementation may resume immediately after the operational
  verification matrix passes.


---

# ADR-011 — Operational Release, Shared Validation and Hybrid Handoff

Status: Accepted
Date: 2026-07-24

## Context

Curvature Console now has a shared implementation for Project, Core and
Research, 118 passing automated tests and a live-verified Core Thread
Handoff. Continuing broad Console development would delay work on Project
Curvature without a demonstrated operational need.

New ChatGPT conversation creation may be slow. The visible Chrome window is part
of the approved hybrid model and provides observation or intervention without
replacing the automated workflow.

## Decision

Curvature Console is operational for normal Project Curvature development.

Shared features are:

- implemented once;
- covered by automated department-isolation tests;
- deeply live-validated in Core;
- smoke-tested in Project or Research when a change is department-specific,
  configuration-sensitive or evidence indicates a route defect.

A separate three-department live repetition is not mandatory for every shared
change.

The browser workflow is hybrid:

- automation is the default;
- ordinary Chrome may become visible;
- new-chat creation may take longer than an existing-thread task;
- Console waits while verified progress continues;
- the previous route and transcript remain authoritative until the new `/c/...`
  route and first response are verified.

## Consequences

- broad Console feature development stops;
- real Curvature work resumes through Console;
- structured records, expanded State Bus, unified tracing and UX refinements are
  deferred until required;
- no reduction is made to repository-write approval, department isolation,
  routing safety, test requirements or the zero-additional-cost rule.


---

# ADR-016 — Invisible Full Chrome, Runtime Heartbeat and Owned Cleanup

Status: Accepted
Date: 2026-07-26

## Context

Chromium headless mode received a Cloudflare `Just a moment...` page and could
not expose the ChatGPT composer. Visible Chrome interrupted the desktop. The
user also required clear visual proof that Console remained responsive during
long browser work.

## Decision

Normal browser automation uses a full Google Chrome process inside Xvfb.

Every exchange:

- owns an immutable request identifier;
- uses one dedicated page;
- binds to an exact persisted conversation URL;
- confirms the current user message through a unique marker;
- displays an indeterminate progress bar, current stage and elapsed time;
- writes a timestamped runtime log;
- terminates the complete Console-owned Chrome/Xvfb process group;
- verifies release of CDP port 9222.

Visible Chrome is reserved for confirmed login or human verification.

## Consequences

- normal automation remains invisible on the physical desktop;
- Cloudflare sees a normal headed browser environment;
- the user can distinguish active work from a frozen UI;
- failures have durable diagnostic evidence;
- orphan browser processes are detected and cleaned up.

---

# ADR-017 — Generated Downloads Are Format-Agnostic

Status: Accepted
Date: 2026-07-26

## Context

ChatGPT may generate text, Markdown, JSON, CSV, PDF, image, office-document,
archive and other file types. Treating every generated file as ZIP corrupts
meaning and incorrectly couples download capture to deployment-package review.

## Decision

Generated-file capture preserves the actual safe filename and extension supplied
by the download.

No fixed extension is imposed.

Package Review remains a separate workflow for supported deployment packages.

## Consequences

- `.txt` remains `.txt`;
- ZIP is one supported download type, not the universal type;
- arbitrary generated files can be stored and traced;
- package validation is not applied to ordinary downloads.


---

# ADR-018 — Assistant-Response-Scoped Download Capture

Status: Accepted
Date: 2026-07-26

Generated-file discovery is restricted to the newly completed assistant message
for the active request.

The browser-suggested filename is authoritative after path sanitisation. Storage
uses collision-safe suffixes while preserving the extension.

Individual download failures are logged and do not invalidate an otherwise
successful text response.

---

# ADR-019 — Complete Assistant-Turn File Discovery

Status: Accepted
Date: 2026-07-26

Generated-file controls may be siblings of the assistant text node. Discovery
therefore scopes to the complete assistant conversation turn and inspects links,
buttons, role buttons and file-card metadata.

Empty capture writes bounded candidate and DOM diagnostics.

---

# ADR-020 — Two-Stage Generated-File Interaction

Status: Accepted
Date: 2026-07-26

A generated-file card is not assumed to be the final download control. Console
first attempts direct capture, then searches a newly opened preview for the real
Download action.

# ADR-012 — Generated-File Fetch Capture

Status: Accepted
Date: 2026-07-28

## Context

Live B5.R2D2 verification showed that a ChatGPT generated-file card can deliver
its payload through a successful `/backend-api/estuary/content` fetch response
without emitting a native Playwright download event.

## Decision

The browser bridge supports two verified capture channels:

1. native browser download events when present;
2. HTTP 200 attachment responses, including Estuary content responses.

The final response body is saved through the same filename sanitisation,
collision handling, department isolation and provenance pipeline.

Controls labelled `Coding Citation` are not generated-file candidates.

## Consequences

- generated non-ZIP files can be captured reliably;
- browser-engine replacement is not required for this delivery mechanism;
- attachment response handling remains UI-dependent and requires explicit
  failure logging when ChatGPT changes its delivery flow.

# ADR-013 — Supervised Handoff Aggregate

Status: Accepted
Date: 2026-07-29

## Context

Interdepartmental communication must remain visible, attributable and under
user control. A browser message alone is insufficient because it does not
preserve lifecycle state or the complete correspondence timeline.

## Decision

A handoff is an immutable domain aggregate identified by `handoff_id` and linked
to its originating `request_id`. It records source, target, lifecycle state,
timestamps, the user-visible instruction and an ordered visible timeline.

Only Project, Core and Research may participate. Source and target must differ.
Lifecycle transitions are explicit and terminal states cannot be reopened.

SQLite stores the aggregate and timeline atomically. This foundation does not
send messages, change routes or add automation.

## Consequences

- restart-safe supervised communication has a stable backend model;
- invalid routing and lifecycle jumps fail before browser activity;
- later approval UI can operate on one deterministic state machine;
- controlled automation remains a later, separately approved layer.

# ADR-014 — Approval Is Not Delivery

Status: Accepted
Date: 2026-07-29

## Decision

A supervised handoff enters an explicit `approved` state before it may enter
`sent`. B5.5B may create and approve records, but it may not perform browser
delivery.

All user control actions are persisted as visible timeline messages. Redirect
is limited to draft, pending-approval and held records. Editing is limited to
drafts. Terminal states remain closed.

## Consequences

- user approval cannot silently trigger a browser send;
- B5.5C can implement delivery as a separate audited transition;
- restart continuity preserves both state and control history.


# ADR-015 — One-Shot Approved Handoff Delivery

Status: Accepted
Date: 2026-07-29

## Decision

An approved interdepartmental handoff may be delivered exactly once only after a
separate visible user confirmation. Delivery uses the target department's exact
persisted conversation URL and remains bound to immutable request and handoff
identifiers.

Success records the returned answer in the handoff timeline. Failure transitions
the handoff to held with a visible reason. Approval does not create an autonomous
loop, and Console does not continue the conversation in the background.

## Consequences

- Project, Core and Research can exchange a supervised message through Console;
- the user remains the mandatory gate before delivery;
- failed delivery is recoverable without losing the handoff record;
- multi-turn or autonomous departmental communication remains outside this ADR.

# ADR-018 — Bound Normal Task Context, Not Browser Input

Status: Accepted
Date: 2026-07-29

Evidence showed no browser-entry code difference between the last live-passing
commit and B5.5C. The changed input was the unbounded authoritative context:
the same builder embedded two Markdown documents whose combined size increased.

Normal Task packages therefore use a fixed 12,000-character authoritative
section budget and omit additional whole documents rather than truncating them.
The current-state document has priority. Full continuity belongs to Thread
Handoff mode.

# ADR-019 — Separate Reply Status from Reply Reading

Status: Accepted
Date: 2026-07-30

## Decision

Department panels show compact reply availability rather than rendering the full
transcript inline. Full tasks and replies remain persisted and are read through a
dedicated, resizable per-department Reply Viewer.

The persisted transcript remains the source for normal Task context, Thread
Pressure and Thread Handoff. Replacing inline transcript display must not replace
or truncate the underlying stored conversation.

## Consequences

- long responses no longer crowd the three-panel workspace;
- users can inspect current and earlier replies on demand;
- restart continuity and context construction remain unchanged;
- reply presentation and transcript persistence remain separate concerns.

# ADR-017 — Department-Generated Handoff Proposals

Status: Accepted and implemented
Date: 2026-07-30

## Decision

Every Curvature department may propose work for any other department through a
strict delimited JSON envelope in its normal assistant response. Console binds
the source to the originating department, validates the proposed target and
content, and persists the result as supervised `PENDING_APPROVAL` in the shared
Communication Hub. Manual drafts continue to use `DRAFT`.

A proposal is not delivery. Console must not automatically request approval,
approve, deliver, return a response or continue a cross-department loop. The
user remains the mandatory gate at every department boundary.

Manual draft creation remains a fallback and diagnostic control.


# ADR-018 — Department-Generated Proposals Enter Pending Approval

Status: Accepted and implemented
Date: 2026-07-30

## Decision

A validated proposal generated by a department enters the Supervised
Communication Hub directly as `PENDING_APPROVAL`. Requiring the sole operator to
request approval from themselves adds no control and duplicates the actual
approval decision.

Manual drafts continue to begin as `DRAFT` because their content may still be
under construction.

## Consequences

- department-generated proposals require one explicit `Approve` decision;
- no proposal is approved or delivered automatically;
- manual draft editing remains available;
- the persisted lifecycle still distinguishes working draft, pending approval,
  approved and delivered states.

# ADR-019 — Evidence-Based Browser Delivery Confirmation

Status: Accepted and implemented
Date: 2026-07-30

## Decision

Browser delivery must use multiple bounded pieces of evidence rather than one
DOM counter. Message entry uses the verified ProseMirror keyboard path. Submit
clicks the active Send button first and uses Enter only as fallback. Successful
submission may be confirmed by a current request marker or a new assistant turn.
Assistant replies are identified by stable message identity and captured only
after completion.

## Consequences

- virtualised ChatGPT DOM counts are not treated as authoritative on their own;
- successful sends do not become false `HELD` failures;
- failed sends remain explicit and held;
- no retry loop may create duplicate department messages.

# ADR-020 — Timestamped Snapshot Archive

Status: Accepted and implemented
Date: 2026-07-30

## Decision

Repository snapshots are written as one timestamped ZIP under
`data/snapshots/`. Historical snapshots are retained. `latest.zip` is a symlink
to the latest timestamped archive rather than a duplicate copy. Snapshot output
must exclude the snapshot archive itself.
