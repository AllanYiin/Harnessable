from harnessable.events import EventType, HarnessEvent
from harnessable.resilience import FailureCategory, FailureLayer, FailureSignal, FallbackManager, FallbackPolicy, FallbackPolicyRegistry


def test_fallback_e2e_timeout_retry_route():
    event = HarnessEvent(event_id="evt", run_id="run", event_type=EventType.TOOL_CALL_FAILED, capability={"type": "TOOL"})
    registry = FallbackPolicyRegistry()
    registry.add(
        FallbackPolicy(
            id="fb",
            name="FB",
            applies_to={"event_types": ["TOOL_CALL_FAILED"], "capability_types": ["TOOL"]},
            constraints={"max_total_attempts": 3},
            fallback_graph=[
                {"id": "retry", "action": {"type": "RETRY"}},
                {"id": "route", "action": {"type": "ROUTE", "selector": {"same_or_stricter_permission_boundary": True}}},
            ],
        )
    )
    signal = FailureSignal(run_id="run", event_id="evt", layer=FailureLayer.TOOL, category=FailureCategory.TIMEOUT)
    plan = FallbackManager(registry).plan(event, signal)
    assert [step.action_type for step in plan.steps] == ["RETRY", "ROUTE"]
