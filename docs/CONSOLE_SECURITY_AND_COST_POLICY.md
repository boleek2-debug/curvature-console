# Console Security and Cost Policy

Status: Approved
Version: 1.0.0
Owner: Curvature Console Development Unit

## Cost policy

Normal Console operation must not cost more than the existing ChatGPT Plus subscription.

- no mandatory paid API;
- no hidden paid request;
- no automatic paid retry;
- paid providers are optional, disabled by default and require explicit approval;
- cost and data destination must be shown before use;
- a local or free fallback is preferred where practical.

## Repository safety

- no silent apply;
- no automatic commit or push;
- no force push;
- repository target and branch must be explicit;
- package paths must be repository-relative and traversal-safe;
- backups and rollback are required for controlled writes;
- runtime files must remain outside Git or be ignored.

## Command safety

- command execution uses an allowlist and explicit working directory;
- arbitrary shell commands from chat text are prohibited;
- environment, timeout, cancellation and exit code must be visible;
- stdout, stderr and execution records must be retained.

## Browser and credential safety

- Browser Bridge uses the user's local logged-in Chrome profile;
- CDP binds locally;
- cookies and credentials never enter source control;
- login expiry, CAPTCHA and UI changes are visible failures;
- automation must not bypass official user controls.

## Data boundaries

- attachments and downloads remain department- or unit-scoped;
- credentials, private source files and browser state are never included in generated packages;
- external network access must be declared by the workflow;
- every external provider must record privacy, licence and cost implications.
