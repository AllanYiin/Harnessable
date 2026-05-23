from harnessable import HarnessKernel
from harnessable.events import EventType, HarnessEvent
from harnessable.evals import ReplayEngine


def test_replay_detects_rule_diff():
    kernel = HarnessKernel()
    event = HarnessEvent(event_id="evt", run_id="run", event_type=EventType.RUN_STARTED).to_dict()
    diff = ReplayEngine(kernel).diff([event], [{"effect": "BLOCK"}])
    assert diff["changed"] is True
