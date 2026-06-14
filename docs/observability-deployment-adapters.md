# Observability and Deployment Adapters

Stage 22 adds exporter and deployment seams for self-hosted integrations while
keeping core dependencies optional.

## Exporters

`JsonlTraceExporter` exports sanitized Harnessable trace records as JSONL. It
preserves event and decision metadata but removes sensitive top-level fields such
as `payload`, `content`, `secret`, `token`, `password`, `api_key`, and
`authorization`.

`OpenTelemetryStyleTraceExporter` emits an OpenTelemetry-style
`resourceSpans -> scopeSpans -> spans` payload. This is a dependency-free shape
adapter, not a claim of full OpenTelemetry SDK compliance. It lets teams route
Harnessable evidence into existing telemetry pipelines through an adapter that
can later speak OTLP.

## Deployment Store Adapter

`ProjectStoreAdapter` is the remote/local store seam. `LocalProjectStoreAdapter`
implements the contract for existing local projects and supports migration
dry-run reports:

- current version
- target version
- migration required
- planned actions
- limitations

The dry run is read-only. Remote database adapters must implement the same report
shape before being used in deployment flows.

## Self-Host Notes

Docker, Kubernetes, remote databases, backup jobs, retention policies, and
schema migrations belong in adapters or deployment examples. Core tests must not
require those systems.

Backups should include:

- project manifest
- runs JSONL
- eval cases
- trace promotion previews/results
- audit packages
- imported artifact metadata and hashes

Retention policies should prefer deletion by run, artifact, and audit package
refs rather than ad hoc file deletion.

## Verification

```bash
python -m pytest tests/test_observability_exporters.py tests/test_docs_contract.py
python -m compileall src
```
