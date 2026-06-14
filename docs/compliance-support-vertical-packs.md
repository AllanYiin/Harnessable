# Compliance Support and Vertical Packs

Stage 24 adds evidence mapping exports and reusable vertical pack skeletons. The
feature is intentionally named compliance support: Harnessable can organize
evidence, but it does not provide legal advice, certification, or a compliance
guarantee.

## Evidence Mapping Exports

The export helpers produce support matrices for:

- NIST AI RMF style functions: govern, map, measure, manage
- ISO/IEC 42001 support areas: policy, risk treatment, monitoring
- EU AI Act high-risk support checklist areas: risk management, logging, human
  oversight, technical documentation

Every entry uses `supports_evidence_for` wording and includes evidence refs plus
limitations.

## Vertical Harness Packs

Built-in pack skeletons:

- `coding`
- `research`
- `ops`

Packs contain profile metadata, default rule refs, default capability refs,
evidence-support claims, and limitations. They do not install automatically.

## Preview / Apply

`VerticalPackStore.preview(pack)` writes a preview artifact with a source hash and
warnings. `VerticalPackStore.apply(preview_id)` revalidates the hash before
writing the pack into the project.

This mirrors Harnessable import policy: mutating configuration flows must preview
before apply.

## Verification

```bash
python -m pytest tests/test_compliance_vertical_packs.py tests/test_docs_contract.py
python -m compileall src
```
