# Console Test Matrix

Status: Active
Version: 1.0.0
Owner: Curvature Console Development Unit

## Current regression areas

| Area | Automated | Live | Required evidence |
|---|---:|---:|---|
| Department routing | Yes | Yes | exact URL and origin panel |
| CDU routing/migration | Yes | Yes | same conversation and preserved state |
| Attachments | Yes | Yes | single, multiple, screenshot, failure-before-send |
| Generated downloads | Yes | Yes | filename, collision handling, department inbox |
| Package review/apply | Yes | Yes | classification, backup, rollback, result metadata |
| Handoffs | Yes | Yes | lifecycle, delivery, return, same identity |
| Restart continuity | Yes | Yes | drafts, routes, records, attachments |
| Git safety | Partial | Manual | no unintended runtime files or push |
| Cost safeguards | Policy | Manual | no paid provider without approval |

## Future adapter tests

Every adapter requires:

- discovery and version detection;
- health check;
- valid invocation;
- invalid input rejection;
- timeout and cancellation;
- retry safety;
- stdout/stderr or equivalent logs;
- artifact registration;
- licence/cost metadata;
- restart recovery where applicable.

## Release gate

A milestone closes only when automated validation, `git diff --check`, expected file scope and required live workflow evidence all pass.

## CDU-004 automatic escalation

- valid Console request envelope parses;
- unsupported request type is rejected;
- every department package includes automatic escalation instructions;
- automatic CDU request preserves source department and source request ID;
- CDU result is queued back to the source department;
- captured artifact paths are included in the return;
- shared queue prevents parallel Browser Bridge workers;
- operator approval remains required for controlled actions;
- documentation closure is present in the CDU execution prompt.

## CDU-004A

- identical artifact exposed through fetch and native-download channels is captured once;
- collision suffixes such as `(1)` and local `-2` do not create a second logical artifact when content hashes match;
- escalation chain preserves source request, chain ID and attempt number;
- one corrective CONSOLE_DEFECT attempt receives latest snapshot and runtime log;
- third automatic escalation is blocked and surfaced for operator action.
## 2026-08-05 CDU-004A live evidence

- automatic Core request detection: PASS;
- automatic Core → CDU routing: PASS;
- generated artifact capture: PASS;
- equivalent fetch/native capture suppression by SHA-256: PASS;
- logical artifact count equals one: PASS;
- automatic CDU → Core return: PASS;
- Core exact filename/content/hash verification and acceptance: PASS;
- escalation loop prevention in the successful path: PASS;
- full automated suite: 243 passed;
- `git diff --check`: PASS.

## Planned Console-first acceptance areas

Future milestones must add regression and live coverage for durable operational conversations, notification suppression, Conversation Review, Accept/Reject/Ask continuation, operator-owned vision gates, restart recovery and complete multi-department Console-first execution.

## CDU-004B1 operational conversation foundation

- SQLite operational conversation create/update/load: targeted automated PASS in packaging environment.
- Ordered durable transcript: targeted automated PASS in packaging environment.
- Result-ready review counter: targeted automated PASS in packaging environment.
- Qt review dialog and full regression suite: required in project Conda environment.
- Live automatic Core → CDU → Core transcript capture across restart: required before milestone closure.
## CDU-004B2 Operator Review
- Persist operator-authored transcript entries and terminal ACCEPTED state.
- Accept without mandatory comment.
- Reject and Ask / Continue require operator text.
- Reject and Ask preserve conversation ID and source request ID when routed back.
- Review count excludes accepted conversations.
- Live Accept, Ask / Continue and Reject tests: PASS.

## CDU-004B2A

- Same operational conversation reused across Ask / Continue: automated coverage added.
- Source request remains stable while technical request IDs change: covered by persistence test.
- Round count increments without duplicating transcript records: automated coverage added.
- Result-ready and closure timestamps persist: automated coverage added.
- Lifecycle details visible in Operator Review: target-environment live test required.
## CDU-004B2B
- Exact confirmed assistant message selected by message ID: automated PASS.
- Stale file card from earlier round excluded from capture scope: regression covered.
- Live stage-one → Ask/Continue → stage-two artifact-content test: PASS.

## CDU-004B2C

- Logical artifact filename extraction and deduplication: automated PASS.
- Unique transport filename differs between rounds and requests: automated PASS.
- Exact assistant-turn capture remains required: covered by CDU-004B2B regression tests.
- Stale logical-name attachment rejection: PASS through unique transport identity.
- Transport-to-logical local mapping with Console-calculated byte count and SHA-256: live PASS.
- Live stage-one → Ask/Continue → stage-two artifact-content test: PASS.
- Live Reject → corrected stage-two artifact test: PASS.
- Full target suite: 251 passed.
- `git diff --check`: PASS.

## CDU-004B3

- Explicit RESULT / BLOCKER / OPERATOR_DECISION markers: targeted automated PASS.
- Conservative blocker and operator-decision phrase fallback: targeted automated PASS.
- Normal completed response defaults to RESULT: targeted automated PASS.
- Attention kind and reason persist in SQLite: targeted automated PASS.
- Review counts grouped by attention kind: targeted automated PASS.
- Full Qt regression suite: required in the project Conda environment because PySide6 is unavailable in the packaging environment.
- Live verification must demonstrate one result, one blocker and one operator-decision response without modal noise during internal transitions.
