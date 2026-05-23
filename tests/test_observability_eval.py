from harnessable import HarnessKernel
from harnessable.evals import EvalCase, EvalRunner, ReplayEngine, ReplayReport
from harnessable.events import EventType, HarnessEvent


def test_trace_audit_metrics_and_eval_runner():
    kernel = HarnessKernel()
    case = EvalCase(
        id="allow",
        event=HarnessEvent(event_id="evt_1", run_id="run_1", event_type=EventType.RUN_STARTED).to_dict(),
        expected_effect="ALLOW",
    )
    results = EvalRunner(kernel).run([case])
    assert results[0]["passed"] is True
    assert kernel.traces.by_kind("event")
    assert kernel.audit.by_kind("decision")
    assert kernel.metrics.snapshot()["decision.ALLOW"] >= 1


def test_replay_diff_report():
    kernel = HarnessKernel()
    event = HarnessEvent(event_id="evt_1", run_id="run_1", event_type=EventType.RUN_STARTED).to_dict()
    diff = ReplayEngine(kernel).diff([event], baseline_decisions=[{"effect": "BLOCK"}])
    report = ReplayReport(run_id="run_1", decisions=diff["decisions"], baseline_decisions=diff["baseline_decisions"])
    assert report.changed is True
    assert report.to_dict()["changed"] is True
