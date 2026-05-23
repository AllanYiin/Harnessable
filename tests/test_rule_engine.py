from harnessable import HarnessKernel
from harnessable.decisions import DecisionEffect
from harnessable.events import EventType, HarnessEvent
from harnessable.rules import ConditionEngine, HarnessRule, RuleRegistry


def tool_event(text="delete all"):
    return HarnessEvent(
        event_id="evt_1",
        run_id="run_1",
        event_type=EventType.TOOL_CALL_REQUESTED,
        runtime_type="agent",
        hook_point="before_tool_call",
        actor={"role": "assistant"},
        capability={"type": "TOOL"},
        payload={"text": text},
    )


def test_condition_engine_all_any_not():
    engine = ConditionEngine()
    event = tool_event()
    assert engine.evaluate({"all_of": [{"field": "runtime_type", "equals": "agent"}, {"field": "payload.text", "contains": "delete"}]}, event)
    assert engine.evaluate({"any_of": [{"field": "runtime_type", "equals": "chat"}, {"field": "capability.type", "equals": "TOOL"}]}, event)
    assert engine.evaluate({"not": {"field": "runtime_type", "equals": "chat"}}, event)


def test_rule_registry_lifecycle_and_matching():
    registry = RuleRegistry()
    rule = HarnessRule(
        id="tool_block",
        name="Block delete",
        applies_to={"event_types": ["TOOL_CALL_REQUESTED"], "runtimes": ["agent"], "capability_types": ["TOOL"]},
        hook={"point": "before_tool_call"},
    )
    registry.add(rule)
    assert registry.match(tool_event()) == [rule]
    registry.disable(rule.id)
    assert registry.match(tool_event()) == []
    registry.enable(rule.id)
    registry.shadow(rule.id)
    assert registry.match(tool_event())[0].shadow is True
    registry.archive(rule.id)
    assert registry.match(tool_event()) == []


def test_rule_engine_regex_block_and_shadow():
    kernel = HarnessKernel()
    kernel.register_rule(
        HarnessRule(
            id="regex_block",
            name="Regex block",
            applies_to={"event_types": ["TOOL_CALL_REQUESTED"], "runtimes": ["agent"], "capability_types": ["TOOL"]},
            detector={"type": "regex", "field": "payload.text", "pattern": "delete"},
            action={"when_detected": {"type": "BLOCK"}, "when_clean": {"type": "ALLOW"}},
        )
    )
    decision = kernel.emit(tool_event())
    assert decision.effect == DecisionEffect.BLOCK

    kernel.rules.shadow("regex_block")
    decision = kernel.emit(tool_event())
    assert decision.effect == DecisionEffect.ALLOW
    assert decision.contributing_decisions[0]["shadow"] is True
