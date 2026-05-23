import pytest

from harnessable.capabilities import CapabilityProfile, CapabilityType
from harnessable.core import ValidationError
from harnessable.decisions import DecisionEffect, HarnessDecision
from harnessable.decisions.priority import priority
from harnessable.events import EventType, HarnessEvent
from harnessable.resilience import FallbackPolicy, FailureCategory, FailureLayer, FailureSignal
from harnessable.rules import HarnessRule
from harnessable.state import ProjectManifest


def test_core_models_round_trip():
    event = HarnessEvent(event_id="evt_1", run_id="run_1", event_type=EventType.USER_INPUT_RECEIVED)
    assert HarnessEvent.from_dict(event.to_dict()).event_type == EventType.USER_INPUT_RECEIVED

    decision = HarnessDecision(event_id="evt_1", effect=DecisionEffect.BLOCK)
    assert HarnessDecision.from_dict(decision.to_dict()).effect == DecisionEffect.BLOCK

    rule = HarnessRule(id="rule_1", name="Rule")
    assert HarnessRule.from_dict(rule.to_dict()).id == "rule_1"

    cap = CapabilityProfile(id="tool.search", type=CapabilityType.TOOL)
    assert CapabilityProfile.from_dict(cap.to_dict()).type == CapabilityType.TOOL

    signal = FailureSignal(run_id="run_1", event_id="evt_1", layer=FailureLayer.TOOL, category=FailureCategory.TIMEOUT)
    assert FailureSignal.from_dict(signal.to_dict()).category == FailureCategory.TIMEOUT

    policy = FallbackPolicy(id="fb_1", name="Fallback", constraints={"max_total_attempts": 1})
    assert FallbackPolicy.from_dict(policy.to_dict()).id == "fb_1"

    manifest = ProjectManifest(name="Demo")
    assert ProjectManifest.from_dict(manifest.to_dict()).name == "Demo"


def test_validation_errors_and_priority():
    with pytest.raises(ValidationError):
        HarnessEvent(event_id="", run_id="run", event_type=EventType.RUN_STARTED)
    with pytest.raises(ValidationError):
        HarnessRule(id="", name="bad")
    with pytest.raises(ValidationError):
        FallbackPolicy(id="fb", name="bad")
    with pytest.raises(ValidationError):
        CapabilityProfile(id="action.send", type=CapabilityType.EXTERNAL_ACTION)

    assert priority(DecisionEffect.BLOCK) > priority(DecisionEffect.TRANSFORM) > priority(DecisionEffect.ALLOW)
    assert EventType.PLAN_PROPOSED.value == "PLAN_PROPOSED"
