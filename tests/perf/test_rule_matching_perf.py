import time

from harnessable.events import EventType, HarnessEvent
from harnessable.rules import HarnessRule, RuleRegistry


def test_rule_matching_perf_under_threshold():
    registry = RuleRegistry()
    for index in range(500):
        registry.add(
            HarnessRule(
                id=f"rule_{index}",
                name=f"Rule {index}",
                applies_to={"event_types": ["TOOL_CALL_REQUESTED"], "capability_types": ["TOOL"]},
            )
        )
    event = HarnessEvent(event_id="evt", run_id="run", event_type=EventType.TOOL_CALL_REQUESTED, capability={"type": "TOOL"})
    started = time.perf_counter()
    matched = registry.match(event)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert len(matched) == 500
    assert elapsed_ms < 20
