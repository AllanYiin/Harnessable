import json

from harnessable import AuditPackageExporter, HarnessKernel, HarnessProject
from harnessable.cli.main import main
from harnessable.events import EventType, HarnessEvent


def test_audit_package_exports_run_refs_hashes_and_redacts_secrets(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Audit Project")
    artifact_id = project.artifacts.create({"result": "ok"}, {"owner": "qa"})
    kernel = HarnessKernel.from_project(project)
    kernel.emit(
        HarnessEvent(
            event_id="evt_tool",
            run_id="run_audit",
            event_type=EventType.TOOL_CALL_REQUESTED,
            payload={
                "artifact_refs": [artifact_id],
                "api_token": "should-not-leak",
                "nested": {"password": "hidden"},
            },
        )
    )

    package = AuditPackageExporter(project).export_run(
        "run_audit",
        eval_refs=["eval://case-1"],
        replay_refs=["replay://run_audit"],
        created_at="2026-06-14T00:00:00+00:00",
        package_id="audit_fixed",
    )

    data = package.to_dict()
    serialized = json.dumps(data)
    assert data["event_refs"] == ["evt_tool"]
    assert data["decision_refs"] == ["evt_tool"]
    assert data["gateway_call_refs"] == ["evt_tool"]
    assert data["artifact_refs"] == [artifact_id]
    assert data["artifact_hashes"][artifact_id]
    assert data["eval_refs"] == ["eval://case-1"]
    assert data["replay_refs"] == ["replay://run_audit"]
    assert data["redaction_summary"]["redacted_count"] == 2
    assert "should-not-leak" not in serialized
    assert "hidden" not in serialized
    assert data["integrity_hash"] == package.compute_integrity_hash()


def test_audit_package_is_stable_for_fixed_inputs_and_marks_missing_fields_unknown(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Audit Project")
    project.state.append_event(
        "legacy_run",
        {
            "event": {"event_id": "evt_legacy", "run_id": "legacy_run", "event_type": "RUN_STARTED"},
            "decision": {"event_id": "evt_legacy", "effect": "ALLOW"},
        },
    )
    exporter = AuditPackageExporter(project)

    first = exporter.export_run("legacy_run", created_at="2026-06-14T00:00:00+00:00", package_id="audit_fixed")
    second = exporter.export_run("legacy_run", created_at="2026-06-14T00:00:00+00:00", package_id="audit_fixed")
    missing = exporter.export_run("missing_run", created_at="2026-06-14T00:00:00+00:00", package_id="audit_missing")

    assert first.to_dict() == second.to_dict()
    assert first.integrity_hash == second.integrity_hash
    assert missing.to_dict()["event_refs"] == ["unknown"]
    assert missing.to_dict()["decision_refs"] == ["unknown"]
    assert "no_run_records" in missing.to_dict()["warnings"]


def test_cli_audit_export_outputs_package(tmp_path, capsys):
    project = HarnessProject.create(str(tmp_path / "project"), "CLI Audit")
    kernel = HarnessKernel.from_project(project)
    kernel.emit(HarnessEvent(event_id="evt_cli", run_id="run_cli", event_type=EventType.RUN_STARTED))

    assert main(["audit", "--project", str(project.path), "export", "run_cli"]) == 0
    data = json.loads(capsys.readouterr().out)

    assert data["run_id"] == "run_cli"
    assert data["event_refs"] == ["evt_cli"]
    assert data["integrity_hash"]

