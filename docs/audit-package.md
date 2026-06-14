# Audit Package

`AuditPackage` is the Stage 16 evidence export surface. It packages run evidence
without changing rule decisions or gateway behavior.

The package records:

- run and project identity
- source trace refs
- event refs
- decision refs
- gateway call refs
- approval refs
- artifact refs and artifact file hashes
- eval, replay, policy pack, and lineage refs
- redacted run records
- redaction summary
- warnings for missing legacy evidence
- package integrity hash

Missing fields from older runs are represented as `unknown` or explicit
warnings. The exporter must not fabricate evidence.

## Library API

```python
from harnessable import AuditPackageExporter, HarnessProject

project = HarnessProject.open("./demo-project")
package = AuditPackageExporter(project).export_run("run_1")
data = package.to_dict()
```

## CLI

```bash
python -m harnessable.cli.main audit --project ./demo-project export run_1
```

## Boundary

The audit package is a sidecar evidence artifact. It does not:

- change `HarnessDecision` semantics
- execute replay automatically
- store raw secret values
- duplicate large artifact payloads by default
- claim legal compliance by itself

## Verification

```bash
python -m pytest tests/test_audit_package.py tests/test_docs_contract.py
```

