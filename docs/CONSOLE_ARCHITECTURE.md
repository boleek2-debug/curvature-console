# Console Architecture

Status: Approved baseline
Version: 1.0.0
Owner: Curvature Console Development Unit

## Runtime architecture

Curvature Console is a PySide6 desktop application with SQLite persistence, YAML/Markdown configuration, Playwright browser automation and local filesystem artifact storage.

## Current major components

- Main Window and three permanent department panels;
- Console Development Unit dialog and chat;
- Browser Bridge and worker lifecycle;
- package review and safe apply;
- handoff aggregate, controls and delivery;
- state store and restart continuity;
- diagnostics, logs, snapshots and validation;
- attachments and generated-file capture.

## Planned orchestration components

### Shared Bridge Queue

A durable queue for Project, Core, Research and CDU. Only one exchange controls Chrome at a time. Queue records survive restart.

### Tool Adapter Registry

Every integrated tool declares identity, location, capabilities, inputs, outputs, invocation, health check, cancellation, retry, logs, artefacts, licence, cost and validation.

### Workflow Engine

A workflow combines adapters into ordered stages with approvals, retries, resumability and result return.

### Artifact Registry

Every produced file or directory receives an artifact identifier, provenance, hash, validation status and relationship to requests and runs.

### Execution Ledger

Every run records parameters, stage transitions, timestamps, logs, outputs, failures and operator decisions.

## Extension boundary

CDU may integrate tools required by Project, Core or Research, but the requesting department owns the functional requirement and acceptance contract.
