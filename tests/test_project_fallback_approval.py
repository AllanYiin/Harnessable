import json

from harnessable import HarnessKernel, HarnessProject
from harnessable.decisions import DecisionEffect
from harnessable.approvals import ApprovalManager, ApprovalStatus, InterruptionStore, ResumeController, RunInterruption
from harnessable.events import EventType, HarnessEvent
from harnessable.gateways import SideEffectState, SideEffectTracker
from harnessable.resilience import (
    DegradationBudget,
    FailureCategory,
    FailureLayer,
    FailureSignal,
    FallbackManager,
    FallbackPolicy,
    FallbackPolicyRegistry,
)
from harnessable.state import PROJECT_DIRS, ProjectStatus, RunCheckpoint


def test_project_create_open_preview_apply_and_artifact(tmp_path):
    project_path = tmp_path / "project"
    project = HarnessProject.create(str(project_path), "Demo")
    for dirname in PROJECT_DIRS:
        assert (project_path / dirname).exists()

    reopened = HarnessProject.open(str(project_path))
    assert reopened.manifest.status == ProjectStatus.OPEN

    source = tmp_path / "rule.yaml"
    source.write_text("id: rule_1\nname: Rule\n", encoding="utf-8")
    preview = reopened.import_bundle_preview(str(source))
    assert preview.valid
    assert not (project_path / "rules" / "rule.yaml").exists()
    result = reopened.apply_import(preview.preview_id)
    assert result.applied
    assert (project_path / "rules" / "rule.yaml").exists()
    assert reopened.manifest.status == ProjectStatus.DIRTY
    kernel = HarnessKernel.from_project(reopened)
    assert kernel.rules.get("rule_1").name == "Rule"

    artifact_id = reopened.artifacts.create({"a": 1})
    reopened.artifacts.version(artifact_id, {"a": 2})
    assert reopened.artifacts.read(artifact_id, version=0) == {"a": 1}
    assert reopened.artifacts.read(artifact_id) == {"a": 2}
    reopened.update_metadata(owner="qa")
    assert reopened.manifest.status == ProjectStatus.DIRTY


def test_fallback_timeout_budget_and_side_effect_unknown():
    event = HarnessEvent(event_id="evt_1", run_id="run_1", event_type=EventType.TOOL_CALL_FAILED, capability={"type": "TOOL"})
    registry = FallbackPolicyRegistry()
    registry.add(
        FallbackPolicy(
            id="fb",
            name="fallback",
            applies_to={"event_types": ["TOOL_CALL_FAILED"], "capability_types": ["TOOL"]},
            constraints={"max_total_attempts": 2},
            fallback_graph=[
                {"id": "retry", "level": "L1_LOCAL_RECOVERY", "action": {"type": "RETRY"}},
                {"id": "partial", "level": "L4_PARTIAL_COMPLETION", "action": {"type": "RETURN_PARTIAL"}, "disclosure": {"required": True}},
            ],
        )
    )
    manager = FallbackManager(registry)
    signal = FailureSignal(run_id="run_1", event_id="evt_1", layer=FailureLayer.TOOL, category=FailureCategory.TIMEOUT)
    plan = manager.plan(event, signal)
    assert [step.action_type for step in plan.steps] == ["RETRY", "RETURN_PARTIAL"]
    assert plan.disclosure_required is True

    exhausted = manager.plan(event, signal, DegradationBudget(max_total_attempts=1, attempts=1))
    assert exhausted.decision.effect.value == "FAIL_SAFE"

    unknown = FailureSignal(run_id="run_1", event_id="evt_1", layer=FailureLayer.EXTERNAL_ACTION, category=FailureCategory.SIDE_EFFECT_UNKNOWN)
    assert manager.plan(event, unknown).decision.effect.value == "REQUIRE_APPROVAL"

    registry = FallbackPolicyRegistry()
    registry.add(
        FallbackPolicy(
            id="unsafe",
            name="unsafe",
            applies_to={"event_types": ["TOOL_CALL_FAILED"], "capability_types": ["TOOL"]},
            constraints={"max_total_attempts": 2, "never_degrade": ["tool_permission"]},
            fallback_graph=[
                {
                    "id": "unsafe_route",
                    "action": {
                        "type": "ROUTE",
                        "selector": {"same_or_stricter_permission_boundary": False},
                    },
                }
            ],
        )
    )
    unsafe = FallbackManager(registry).plan(event, signal)
    assert unsafe.decision.effect.value == "BLOCK"


def test_approval_resume_and_side_effect_retry_guard():
    approvals = ApprovalManager()
    request = approvals.create("run_1", "evt_1")
    assert approvals.get(request.id).status == ApprovalStatus.REQUESTED
    assert approvals.approve(request.id).status == ApprovalStatus.APPROVED

    interruption = RunInterruption(request.id, RunCheckpoint("run_1", "evt_1", {"step": 1}))
    store = InterruptionStore()
    store.save(interruption)
    resumed = ResumeController(store).resume_if_approved(interruption, ApprovalStatus.APPROVED)
    assert resumed["resumed"] is True

    tracker = SideEffectTracker()
    tracker.set_state("op_1", SideEffectState.UNKNOWN)
    assert tracker.can_retry("op_1") is False
