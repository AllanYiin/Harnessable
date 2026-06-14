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

Imports must be previewed before they are applied. Preview is a validation gate:
source files must resolve under an allowed import root, use a supported suffix,
fit the configured byte limit, avoid binary payloads, and declare
`schema_version: "1"` for `rules`, `fallback`, `evals`, and `capabilities`
payloads before they pass the corresponding JSON Schema. `apply_import`
revalidates the source path and hash from preview before copying bytes into the
project, so a changed source must be previewed again. Artifacts support
versioning, archiving, purge, and metadata redaction.
