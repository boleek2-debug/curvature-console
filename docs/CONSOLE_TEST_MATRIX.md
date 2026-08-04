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
