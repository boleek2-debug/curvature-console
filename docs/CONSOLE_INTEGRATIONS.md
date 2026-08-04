# Console Integrations Registry

Status: Active
Version: 1.0.0
Owner: Curvature Console Development Unit

## Status values

ACTIVE | VERIFIED | CANDIDATE | PLANNED | DEFERRED | BLOCKED

## Active integrations

### ChatGPT Browser Bridge

- Status: VERIFIED
- Runtime: Google Chrome + Playwright + local CDP
- Cost: existing ChatGPT Plus only
- Inputs: messages, attachments, screenshots, handoff packages
- Outputs: responses and generated files
- Capabilities: URL routing, upload, send, response capture, download capture, abort, logging
- Limitation: one active exchange at a time until shared queue is implemented

### Git repositories

- Status: ACTIVE, controlled
- Repositories: `~/curvature-console`, `~/Curvature`
- Capabilities: status, diff, branch, HEAD/origin comparison, reviewed apply support
- Prohibited: automatic commit, automatic push, force push

### Local validation

- Status: VERIFIED
- Tools: Bash, Conda, Python, pytest, `git diff --check`, validation scripts
- Outputs: timestamped validation logs and exit codes

### Files, packages and snapshots

- Status: VERIFIED
- Capabilities: attachments, screenshot paste, generated downloads, package review, safe apply, backup, rollback, snapshots

## Planned integrations

### Shared command runner

- Status: PLANNED
- Purpose: safe allowlisted local process execution with logs, timeout and cancel

### ComfyUI

- Status: PLANNED
- Location: remote workstation through existing Curvature runtime
- Purpose: health, queue, workflow invocation, parameterisation, output and provenance capture

### Godot

- Status: PLANNED
- Known runtime: Godot 4.7.1
- Purpose: project registration, run, headless validation, logs, screenshots and test outputs

### Blender

- Status: CANDIDATE
- Purpose: headless import/export, inspection, conversion, technical validation and previews

### Research intake tooling

- Status: PLANNED
- Purpose: source acquisition, access classification, checksum, extraction, citation and Research delivery

### Local language models

- Status: CANDIDATE
- Purpose: offline triage, log classification, local retrieval and low-risk automation
- Policy: supplementary, not an assumed replacement for ChatGPT

## Candidate evaluation fields

Name, purpose, status, location, execution mode, inputs, outputs, formats, licence, cost, hardware, installation, invocation, owner, requester, limitations, validation and fallback.
