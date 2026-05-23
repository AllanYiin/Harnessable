from harnessable.events import EventType, HarnessEvent
from harnessable.resilience import FailureCategory, FailureLayer, FailureSignal, FallbackManager


def test_side_effect_unknown_no_retry():
    event = HarnessEvent(event_id="evt", run_id="run", event_type=EventType.TOOL_CALL_FAILED)
    signal = FailureSignal(run_id="run", event_id="evt", layer=FailureLayer.EXTERNAL_ACTION, category=FailureCategory.SIDE_EFFECT_UNKNOWN)
    assert FallbackManager().plan(event, signal).decision.effect.value == "REQUIRE_APPROVAL"
