# Consequence Gate

`ConsequenceGate` is a generalized release-risk harness. It is not an incident-specific sensitive-word list. Its job is to make unknown social, cultural, political, reputational, and dignity risks visible before an AI-assisted artifact is released.

The gate enforces process invariants:

- release context must be explicit;
- affected stakeholders must be hypothesized;
- reasonable misread paths must be simulated;
- skipped or rushed review must be surfaced;
- approval must include counter-evidence, not just a signature.

## Risk Context

`RiskContext` carries the minimum context needed to judge an externally visible action:

- `jurisdiction`
- `locale`
- `release_at`
- `audience`
- `channel`
- `intent`
- `artifact_refs`
- `ai_generated`
- `known_constraints`
- `review_route`

Missing context is treated as risk. A missing date, locale, audience, publication channel, AI provenance, artifact reference, or approval reason cannot be interpreted as safe.

## Detectors

The built-in consequence detectors are generic:

- `context_gap_detector`: finds missing release context.
- `stakeholder_harm_detector`: requires explicit affected-stakeholder hypotheses.
- `misread_simulator`: requires adversarial, trauma, political, commercialization, and translation/wordplay misread paths.
- `power_asymmetry_detector`: blocks commercial framing around suffering, identity, violence, or unequal power terms.
- `release_pressure_detector`: flags fast-track releases, short deadlines, and skipped reviewers.

These detectors do not encode a specific historical event. Incident feedback should become new risk patterns, replay cases, or detector calibration, not a one-off blacklist.

## Installation

```python
from harnessable import ConsequenceGate, HarnessKernel

kernel = HarnessKernel()
ConsequenceGate.install(kernel)
```

For rollout without blocking:

```python
ConsequenceGate.install(kernel, shadow=True)
```

Shadow decisions are recorded as contributing decisions but do not change the merged decision.

## Publication Gateway

`PublicationGateway` installs `ConsequenceGate` by default and emits `PUBLICATION_REQUESTED` before executing a publisher.

```python
from harnessable import RiskContext
from harnessable.gateways import GatewayContext, PublicationGateway, PublicationRequest

gateway = PublicationGateway(kernel, {"post": lambda **kwargs: "posted"})
result = await gateway.call(
    PublicationRequest(
        name="post",
        content="launch copy",
        destination="social",
        risk_context=RiskContext(
            jurisdiction="GLOBAL",
            locale="en",
            release_at="2026-06-01T09:00:00Z",
            audience=["customers"],
            channel="social",
            intent="brand announcement",
            artifact_refs=["artifact_1"],
            ai_generated=True,
            review_route={"approval_reason": "external publication"},
        ),
        idempotency_key="pub_1",
    ),
    GatewayContext(run_id="run_1"),
)
```

External actions that are not routed through `PublicationGateway` can still be covered by installing `ConsequenceGate` and declaring `public_impact` on the capability risk profile.

## Approval Evidence

Approvals can require counter-evidence:

```python
request = approvals.create(
    "run_1",
    "evt_1",
    reason={
        "requires_counter_evidence": True,
        "required_evidence": ["opened_artifacts", "approval_reason"],
    },
)
approvals.approve(
    request.id,
    {"opened_artifacts": True, "approval_reason": "reviewed risk card and alternate copy"},
)
```

If required evidence is missing, approval fails instead of silently resuming the run.
