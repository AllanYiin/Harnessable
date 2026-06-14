import pytest

from harnessable import ConsequenceGate, HarnessKernel, ProvenanceFinding, RiskContext, RiskFinding, ScannerResult, SimilarityFinding
from harnessable.approvals import ApprovalEvidence, ApprovalManager, ApprovalStatus
from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.core.errors import ValidationError
from harnessable.decisions import DecisionEffect, RuntimeCommandType
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import ActionGateway, GatewayContext, PublicationGateway, PublicationRequest, ToolCallRequest


def complete_context() -> RiskContext:
    return RiskContext(
        jurisdiction="GLOBAL",
        market="GLOBAL",
        locale="en",
        release_at="2026-06-01T09:00:00Z",
        publish_window="2026-06-01T09:00:00Z/2026-06-01T12:00:00Z",
        audience=["customers"],
        channel="social",
        intent="brand announcement",
        campaign_id="cmp_1",
        asset_hash="sha256:test",
        genai_trace_id="gen_1",
        artifact_refs=["artifact_1"],
        ai_generated=True,
        review_route={"approval_reason": "external publication", "reviewers": ["owner"]},
    )


@pytest.mark.asyncio
async def test_publication_missing_context_requires_approval_with_audit_reason():
    kernel = HarnessKernel()
    gateway = PublicationGateway(kernel, {"post": lambda **kwargs: "posted"})

    result = await gateway.call(
        PublicationRequest(
            name="post",
            content="Launch the new AI generated campaign",
            destination="social",
            risk_context=RiskContext(jurisdiction="KR"),
            idempotency_key="pub_1",
        ),
        GatewayContext(run_id="run_pub"),
    )

    assert result.ok is False
    assert result.command.command_type == RuntimeCommandType.REQUEST_APPROVAL
    reason = result.command.payload["decision"]["reason"]
    assert "release_at" in reason["missing_context"]
    assert "audience" in reason["missing_context"]
    assert reason["risk_hypotheses"]


@pytest.mark.asyncio
async def test_public_action_gateway_cannot_bypass_consequence_gate():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    capability = CapabilityProfile(
        id="action.social",
        type=CapabilityType.EXTERNAL_ACTION,
        risk={"side_effect": True, "public_impact": True},
    )
    called = False

    def publish(content: str = ""):
        nonlocal called
        called = True
        return content

    gateway = ActionGateway(kernel, {"publish": publish}, capability=capability)
    result = await gateway.call(
        ToolCallRequest("publish", {"content": "post this"}, idempotency_key="action_1"),
        GatewayContext(run_id="run_action"),
    )

    assert result.ok is False
    assert result.command.command_type == RuntimeCommandType.REQUEST_APPROVAL
    assert called is False


def test_unknown_publication_risk_generates_stakeholder_and_misread_hypotheses():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    event = HarnessEvent(
        event_id="evt_unknown",
        run_id="run_unknown",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "A launch slogan with a local pun!", "risk_context": complete_context().to_dict()},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert decision.reason["affected_stakeholders"]
    assert decision.reason["misread_paths"]
    assert "wordplay amplification" in " ".join(decision.reason["misread_paths"])


def test_low_exposure_draft_warns_instead_of_blocking():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    event = HarnessEvent(
        event_id="evt_draft",
        run_id="run_draft",
        event_type=EventType.DRAFT_PROPOSED,
        payload={"content": "early internal draft"},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.WARN
    assert decision.reason["missing_context"]


def test_shadow_mode_records_consequence_findings_without_blocking():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel, shadow=True)
    event = HarnessEvent(
        event_id="evt_shadow",
        run_id="run_shadow",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish without context"},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.ALLOW
    assert decision.contributing_decisions
    assert all(item["shadow"] is True for item in decision.contributing_decisions)
    assert any(item["reason"]["missing_context"] for item in decision.contributing_decisions)


def test_consequence_preview_rules_use_core_ids_and_warn_when_enabled():
    rules = ConsequenceGate.preview_rules()

    assert rules
    assert all(rule.id.startswith("governance.consequence.preview.") for rule in rules)
    assert not any(rule.id.startswith("harnessdiff.") for rule in rules)
    assert {rule.detector["type"] for rule in rules} >= {
        "context_gap_detector",
        "claim_evidence_detector",
        "offer_disclosure_detector",
        "provenance_metadata_detector",
        "scanner_coverage_detector",
        "scanner_result_detector",
        "rollback_readiness_detector",
    }

    kernel = HarnessKernel()
    ConsequenceGate.install_preview(kernel)
    event = HarnessEvent(
        event_id="evt_preview",
        run_id="run_preview",
        event_type=EventType.FINAL_OUTPUT_PROPOSED,
        metadata={"consequence_gate_enabled": True},
        payload={"content": "publishable draft", "risk_context": RiskContext(jurisdiction="KR").to_dict()},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.WARN
    assert "release_at" in decision.reason["missing_context"]
    assert decision.telemetry["preview"] is True


def test_consequence_preview_rules_are_disabled_without_metadata_gate():
    kernel = HarnessKernel()
    ConsequenceGate.install_preview(kernel)
    event = HarnessEvent(
        event_id="evt_preview_disabled",
        run_id="run_preview_disabled",
        event_type=EventType.FINAL_OUTPUT_PROPOSED,
        payload={"content": "publishable draft", "risk_context": RiskContext(jurisdiction="KR").to_dict()},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.ALLOW


def test_consequence_approval_requires_counter_evidence():
    approvals = ApprovalManager()
    request = approvals.create(
        "run_approval",
        "evt_approval",
        reason={"requires_counter_evidence": True, "required_evidence": ["opened_artifacts", "approval_reason"]},
    )

    with pytest.raises(ValidationError):
        approvals.approve(request.id)

    approved = approvals.approve(request.id, {"opened_artifacts": True, "approval_reason": "reviewed risk card and alternate copy"})
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.evidence["opened_artifacts"] is True


def test_scanner_result_contract_round_trips_without_heavy_dependencies():
    result = ScannerResult(
        scanner_id="external_cv",
        findings=[
            RiskFinding(
                type="visual_symbol",
                severity="high",
                message="map boundary requires local review",
                evidence_ref="artifact://poster#map",
            )
        ],
    )
    context = RiskContext(
        jurisdiction="GLOBAL",
        market="GLOBAL",
        locale="en",
        release_at="2026-06-01T09:00:00Z",
        publish_window="2026-06-01T09:00:00Z/2026-06-01T12:00:00Z",
        audience=["customers"],
        channel="social",
        intent="brand announcement",
        asset_hash="sha256:test",
        genai_trace_id="gen_1",
        artifact_refs=["artifact_1"],
        ai_generated=True,
        scanner_results=[result],
        review_route={"approval_reason": "external publication"},
    )

    restored = RiskContext.from_dict(context.to_dict())

    assert context.to_dict()["schema_version"] == "1"
    assert context.to_dict()["scanner_results"][0]["schema_version"] == "1"
    assert context.to_dict()["scanner_results"][0]["findings"][0]["schema_version"] == "1"
    assert restored.scanner_results[0].scanner_id == "external_cv"
    assert restored.scanner_results[0].schema_version == "1"
    assert restored.scanner_results[0].findings[0].type == "visual_symbol"
    assert restored.scanner_results[0].findings[0].schema_version == "1"


def test_risk_context_accepts_legacy_payload_without_schema_version():
    legacy = {
        "jurisdiction": "GLOBAL",
        "scanner_results": [
            {
                "scanner_id": "legacy_scanner",
                "findings": [
                    {
                        "type": "legacy.finding",
                        "severity": "high",
                        "message": "legacy scanner output",
                    }
                ],
            }
        ],
    }

    restored = RiskContext.from_dict(legacy)

    assert restored.schema_version == "1"
    assert restored.scanner_results[0].schema_version == "1"
    assert restored.scanner_results[0].findings[0].schema_version == "1"
    assert restored.scanner_results[0].findings[0].type == "legacy.finding"


def test_similarity_and_provenance_findings_normalize_to_risk_finding_contract():
    result = ScannerResult(
        scanner_id="external_asset_scanner",
        findings=[
            SimilarityFinding(
                matched_asset_ref="stock://image/123",
                similarity_score=0.94,
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

    restored = ScannerResult.from_dict(result.to_dict())

    assert restored.findings[0].type == "similarity.match"
    assert restored.findings[0].metadata["matched_asset_ref"] == "stock://image/123"
    assert restored.findings[1].type == "provenance.review"
    assert restored.findings[1].metadata["required_rights"] == ["attribution", "local_review"]


def test_publication_missing_new_context_fields_requires_approval():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.market = None
    context.publish_window = None
    context.asset_hash = None
    event = HarnessEvent(
        event_id="evt_missing_new_context",
        run_id="run_missing_new_context",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict()},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert "market" in decision.reason["missing_context"]
    assert "publish_window" in decision.reason["missing_context"]
    assert "asset_hash" in decision.reason["missing_context"]


def test_scanner_findings_require_review_without_builtin_ocr_or_cv():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.scanner_results = [
        ScannerResult(
            scanner_id="external_map_scanner",
            findings=[RiskFinding(type="map_boundary", severity="high", message="localized map review required")],
        )
    ]
    event = HarnessEvent(
        event_id="evt_scanner",
        run_id="run_scanner",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict(), "risk_evidence": {"affected_stakeholders": ["customers"], "misread_paths": ["reviewed"]}},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert decision.reason["scanner_findings"][0]["type"] == "map_boundary"


def test_similarity_scanner_finding_surfaces_match_metadata_for_review():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.scanner_results = [
        ScannerResult(
            scanner_id="external_similarity",
            findings=[
                SimilarityFinding(
                    matched_asset_ref="external://campaign/poster",
                    similarity_score=0.91,
                    license_status="unknown",
                    transform_type="minor_edit",
                )
            ],
            metadata={"capabilities": ["similarity"]},
        )
    ]
    event = HarnessEvent(
        event_id="evt_similarity",
        run_id="run_similarity",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict(), "risk_evidence": {"affected_stakeholders": ["customers"], "misread_paths": ["reviewed"]}},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert decision.reason["similarity_matches"][0]["metadata"]["similarity_score"] == 0.91
    assert decision.reason["similarity_matches"][0]["metadata"]["license_status"] == "unknown"


def test_high_risk_asset_without_required_scanner_coverage_requires_approval():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.asset_kind = "poster"
    event = HarnessEvent(
        event_id="evt_missing_coverage",
        run_id="run_missing_coverage",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict(), "risk_evidence": {"affected_stakeholders": ["customers"], "misread_paths": ["reviewed"]}},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert "missing:similarity" in decision.reason["scanner_coverage_gaps"]
    assert "missing:provenance" in decision.reason["scanner_coverage_gaps"]


def test_completed_scanner_coverage_allows_publication_when_other_risk_evidence_is_present():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.asset_kind = "poster"
    context.scanner_results = [
        ScannerResult(scanner_id="ocr_scanner", metadata={"capabilities": ["ocr"]}),
        ScannerResult(scanner_id="cv_scanner", metadata={"capabilities": ["cv"]}),
        ScannerResult(scanner_id="similarity_scanner", metadata={"capabilities": ["similarity"]}),
        ScannerResult(scanner_id="provenance_scanner", metadata={"capabilities": ["provenance"]}),
    ]
    event = HarnessEvent(
        event_id="evt_complete_coverage",
        run_id="run_complete_coverage",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict(), "risk_evidence": {"affected_stakeholders": ["customers"], "misread_paths": ["reviewed"]}},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.ALLOW
    assert decision.reason["scanner_coverage_gaps"] == []


def test_asset_stage_missing_scanner_coverage_warns_before_publication():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.asset_kind = "video"
    event = HarnessEvent(
        event_id="evt_asset_coverage",
        run_id="run_asset_coverage",
        event_type=EventType.ASSET_PROPOSED,
        payload={"content": "draft public video", "risk_context": context.to_dict()},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.WARN
    assert "missing:asr" in decision.reason["scanner_coverage_gaps"]


def test_claim_evidence_detector_requires_evidence_for_regulated_claims():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.claims = [{"type": "health", "text": "15 minutes equals a long walk"}]
    event = HarnessEvent(
        event_id="evt_claim",
        run_id="run_claim",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict(), "risk_evidence": {"affected_stakeholders": ["customers"], "misread_paths": ["reviewed"]}},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert "15 minutes equals a long walk" in decision.reason["claim_gaps"]


def test_offer_disclosure_detector_requires_visible_auto_renew_disclosure():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.offers = [{"id": "free_ticket", "contains_freebie": True, "subscription": {"auto_renew": True}, "disclosure": {"above_the_fold": False}}]
    event = HarnessEvent(
        event_id="evt_offer",
        run_id="run_offer",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict(), "risk_evidence": {"affected_stakeholders": ["customers"], "misread_paths": ["reviewed"]}},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert "free_ticket" in decision.reason["offer_disclosure_gaps"][0]


def test_provenance_detector_requires_ai_trace_and_rights_metadata():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.genai_trace_id = None
    context.rights = {"uses_third_party_assets": True}
    event = HarnessEvent(
        event_id="evt_provenance",
        run_id="run_provenance",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict(), "risk_evidence": {"affected_stakeholders": ["customers"], "misread_paths": ["reviewed"]}},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert "genai_trace_id" in decision.reason["provenance_gaps"]
    assert "rights.source_attribution" in decision.reason["provenance_gaps"]


def test_high_exposure_publication_requires_rollback_plan():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    context = complete_context()
    context.known_constraints = {"high_exposure": True}
    context.rollback_plan = {"owner": "release_owner"}
    event = HarnessEvent(
        event_id="evt_rollback",
        run_id="run_rollback",
        event_type=EventType.PUBLICATION_REQUESTED,
        capability={"type": "EXTERNAL_ACTION"},
        payload={"content": "publish", "risk_context": context.to_dict(), "risk_evidence": {"affected_stakeholders": ["customers"], "misread_paths": ["reviewed"]}},
    )

    decision = kernel.emit(event)

    assert decision.effect == DecisionEffect.REQUIRE_APPROVAL
    assert "kill_switch" in decision.reason["rollback_constraints"]
    assert "fallback_asset" in decision.reason["rollback_constraints"]


def test_high_risk_override_approval_requires_quality_evidence():
    approvals = ApprovalManager()
    request = approvals.create("run_override", "evt_override", reason={"requires_counter_evidence": True, "high_risk_override": True})

    with pytest.raises(ValidationError):
        approvals.approve(request.id, ApprovalEvidence(opened_artifacts=True, approval_reason="looks fine"))

    approved = approvals.approve(
        request.id,
        ApprovalEvidence(
            opened_artifacts=True,
            risk_card_reviewed=True,
            counter_evidence="checked alternate copy and scanner findings",
            reviewer_role="local/context reviewer",
            approval_reason="risk is resolved before release",
            override_expiry="2026-06-02T00:00:00Z",
        ),
    )
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.evidence["risk_card_reviewed"] is True
