# Project Persistence

Local projects use a file-backed layout:

```text
harnessable.project.json
rules/
capabilities/
fallback/
evals/
runs/
artifacts/
imports/
reports/
```

Project operations:

- `HarnessProject.create`
- `HarnessProject.open`
- `HarnessProject.save`
- `HarnessProject.archive`
- `HarnessProject.import_bundle_preview`
- `HarnessProject.apply_import`

Imports must be previewed before they are applied. Artifacts support versioning, archiving, purge, and metadata redaction.
