import pytest

from harnessable import ConsequenceGate, HarnessKernel, RiskContext
from harnessable.approvals import ApprovalManager, ApprovalStatus
from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.core.errors import ValidationError
from harnessable.decisions import DecisionEffect, RuntimeCommandType
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import ActionGateway, GatewayContext, PublicationGateway, PublicationRequest, ToolCallRequest


def complete_context() -> RiskContext:
    return RiskContext(
        jurisdiction="GLOBAL",
        locale="en",
        release_at="2026-06-01T09:00:00Z",
        audience=["customers"],
        channel="social",
        intent="brand announcement",
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
