# ARCHITECTURE DECISIONS

Status: Active  
Version: 1.1.0  
Owner: Project Curvature  
Last Updated: 2026-07-18

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
