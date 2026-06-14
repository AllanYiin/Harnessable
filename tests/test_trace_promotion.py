import json

from harnessable import HarnessKernel, HarnessProject, RolloutGateReport
from harnessable.cli.main import main
from harnessable.evals import ReplayEngine
from harnessable.events import EventType, HarnessEvent


def test_trace_promotion_preview_apply_and_replay(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Trace Promotion")
    kernel = HarnessKernel.from_project(project)
    kernel.emit(
        HarnessEvent(
            event_id="evt_trace",
            run_id="run_trace",
            event_type=EventType.RUN_STARTED,
            payload={"api_token": "redact-me"},
        )
    )
    records = project.state.read_events("run_trace")

    preview = project.trace_promotions.preview("run_trace", records)
    result = project.trace_promotions.apply(preview.preview_id, records)
    case = json.loads((project.path / "evals" / "run_trace_evt_trace.json").read_text(encoding="utf-8"))

    assert result.applied is True
    assert preview.redaction_summary["redacted_count"] == 1
    assert case["expected_effect"] == "ALLOW"
    assert case["metadata"]["promoted_from_trace"] is True
    assert "redact-me" not in json.dumps(case)
    replay = ReplayEngine(HarnessKernel.from_project(project)).diff([case["event"]], baseline_decisions=[{"effect": "BLOCK"}])
    report = RolloutGateReport.from_replay_diff("baseline://old", "candidate://current", replay, report_id="rollout_fixed")
    assert report.to_dict()["pass"] is False
    assert report.to_dict()["changed_decisions"]


def test_trace_promotion_rejects_stale_preview(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Trace Promotion")
    first = {"event": {"schema_version": "1", "event_id": "evt_1", "run_id": "run", "event_type": "RUN_STARTED"}, "decision": {"effect": "ALLOW"}}
    second = {"event": {"schema_version": "1", "event_id": "evt_2", "run_id": "run", "event_type": "RUN_STARTED"}, "decision": {"effect": "ALLOW"}}
    project.state.append_event("run", first)
    preview = project.trace_promotions.preview("run", project.state.read_events("run"))
    project.state.append_event("run", second)

    result = project.trace_promotions.apply(preview.preview_id, project.state.read_events("run"))

    assert result.applied is False
    assert "source run changed after preview" in result.errors[0]


def test_cli_trace_promotion_preview_and_apply(tmp_path, capsys):
    project = HarnessProject.create(str(tmp_path / "project"), "Trace Promotion CLI")
    HarnessKernel.from_project(project).emit(HarnessEvent(event_id="evt_cli_promote", run_id="run_cli_promote", event_type=EventType.RUN_STARTED))

    assert main(["trace", "--project", str(project.path), "promote-preview", "run_cli_promote"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert main(["trace", "--project", str(project.path), "promote-apply", preview["preview_id"]]) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["applied"] is True
    assert (project.path / "evals" / "run_cli_promote_evt_cli_promote.json").exists()

