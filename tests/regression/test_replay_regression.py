import json
from pathlib import Path

from harnessable import HarnessKernel
from harnessable.events import EventType, HarnessEvent
from harnessable.evals import EvalCase, EvalRunner, ReplayEngine
from harnessable.consequence import ConsequenceGate


def test_replay_detects_rule_diff():
    kernel = HarnessKernel()
    event = HarnessEvent(event_id="evt", run_id="run", event_type=EventType.RUN_STARTED).to_dict()
    diff = ReplayEngine(kernel).diff([event], [{"effect": "BLOCK"}])
    assert diff["changed"] is True


def test_consequence_incident_regression_samples_surface_risk_patterns():
    kernel = HarnessKernel()
    ConsequenceGate.install(kernel)
    cases = [
        EvalCase(**case)
        for case in json.loads(Path("tests/fixtures/replay/consequence_incident_regressions.json").read_text(encoding="utf-8"))
    ]

    results = EvalRunner(kernel).run(cases)

    assert results
    assert all(result["passed"] for result in results)
