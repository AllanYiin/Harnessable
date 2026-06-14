# Trace Promotion

Stage 19 adds a preview/apply workflow that promotes historical run traces into
versioned eval cases, then supports replay diff and rollout gate reports.

## Workflow

1. Read run records from `runs/{run_id}.jsonl`.
2. Generate a `TracePromotionPreview`.
3. Redact sensitive fields.
4. Store source hash in the preview.
5. Apply only if the run hash is unchanged.
6. Write eval cases under `evals/`.
7. Use `ReplayEngine.diff(...)` and `RolloutGateReport` to compare decisions.

## CLI

```bash
python -m harnessable.cli.main trace --project ./demo-project promote-preview run_1
python -m harnessable.cli.main trace --project ./demo-project promote-apply trace_preview_...
```

## Boundary

Trace promotion does not change rule decisions. It creates regression evidence
from observed behavior. Stale previews are rejected.

## Verification

```bash
python -m pytest tests/test_trace_promotion.py tests/test_observability_eval.py tests/test_docs_contract.py
```

