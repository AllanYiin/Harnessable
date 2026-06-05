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
- `market`
- `locale`
- `release_at`
- `publish_window`
- `audience`
- `channel`
- `intent`
- `campaign_id`
- `asset_kind`
- `asset_hash`
- `genai_trace_id`
- `artifact_refs`
- `ai_generated`
- `claims`
- `offers`
- `rights`
- `scanner_results`
- `scanner_coverage`
- `rollback_plan`
- `precedent_refs`
- `known_constraints`
- `review_route`

Missing context is treated as risk. A missing market, date, publication window, locale, audience, publication channel, asset hash, AI provenance, artifact reference, or approval reason cannot be interpreted as safe.

`scanner_results` is an adapter contract. Harnessable does not ship OCR, CV, embedding, similarity, reverse-image-search, rights registry, or claim-extraction engines in core. External scanners attach structured findings, and the gate decides whether those findings need review before release.

`scanner_coverage` declares which external scanners must have run for the asset. For high-risk asset kinds such as `poster`, `image`, `video`, `map`, `product_design`, `social_post`, `slogan`, and `ad_creative`, missing scanner coverage is treated as a risk gap instead of evidence of safety.

Similarity and provenance scanners should return normal `RiskFinding` shaped records. Harnessable also provides typed helpers for adapters:

```python
from harnessable import ProvenanceFinding, ScannerResult, SimilarityFinding

scanner_result = ScannerResult(
    scanner_id="external_asset_scanner",
    findings=[
        SimilarityFinding(
            matched_asset_ref="external://campaign/poster",
            similarity_score=0.91,
            license_status="unknown",
            transform_type="minor_edit",
            evidence_ref="scan://similarity/run-1/match-1",
        ),
        ProvenanceFinding(
            source_type="cultural_pattern",
            rights_status="missing",
            required_rights=["attribution", "local_review"],
            source_ref="archive://pattern/456",
        ),
    ],
    metadata={"capabilities": ["similarity", "provenance"]},
)
```

These helpers normalize to `RiskFinding` records with `type="similarity.match"` or `type="provenance.review"`. The scanner implementation remains outside Harnessable.

## Detectors

The built-in consequence detectors are generic:

- `context_gap_detector`: finds missing release context.
- `stakeholder_harm_detector`: requires explicit affected-stakeholder hypotheses.
- `misread_simulator`: requires adversarial, trauma, political, commercialization, and translation/wordplay misread paths.
- `power_asymmetry_detector`: blocks commercial framing around suffering, identity, violence, or unequal power terms.
- `release_pressure_detector`: flags fast-track releases, short deadlines, and skipped reviewers.
- `claim_evidence_detector`: requires evidence ids for regulated or comparative claims.
- `offer_disclosure_detector`: requires visible disclosure for freebie plus auto-renew offers.
- `provenance_metadata_detector`: requires AI trace, rights, and attribution metadata when applicable.
- `scanner_coverage_detector`: requires declared OCR/CV/ASR/similarity/provenance/rights coverage for high-risk asset kinds before publication.
- `scanner_result_detector`: turns high-severity external scanner findings into review requirements.
- `rollback_readiness_detector`: requires a rollback owner, kill switch, and fallback asset for high-exposure publication.

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
            market="GLOBAL",
            locale="en",
            release_at="2026-06-01T09:00:00Z",
            publish_window="2026-06-01T09:00:00Z/2026-06-01T12:00:00Z",
            audience=["customers"],
            channel="social",
            intent="brand announcement",
            asset_hash="sha256:...",
            genai_trace_id="gen_...",
            artifact_refs=["artifact_1"],
            ai_generated=True,
            review_route={"approval_reason": "external publication"},
        ),
        idempotency_key="pub_1",
    ),
    GatewayContext(run_id="run_1"),
)
```

External actions that are not routed through `PublicationGateway` can still be covered by installing `ConsequenceGate` and declaring `public_impact` on the capability risk profile. Rules still only produce `HarnessDecision`; `ExecutionGovernor` remains the only component that converts decisions into runtime control.

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

High-risk overrides can require richer approval memory:

```python
from harnessable.approvals import ApprovalEvidence

request = approvals.create(
    "run_1",
    "evt_1",
    reason={"requires_counter_evidence": True, "high_risk_override": True},
)
approvals.approve(
    request.id,
    ApprovalEvidence(
        opened_artifacts=True,
        risk_card_reviewed=True,
        counter_evidence="reviewed scanner findings and alternate copy",
        reviewer_role="local/context reviewer",
        approval_reason="risk resolved before release",
        override_expiry="2026-06-02T00:00:00Z",
    ),
)
```

## Incident Replay

Incident feedback should become replay fixtures, detector calibration, and rule tests. It should not become a production blacklist of brand names, historical incidents, or sensitive phrases.
