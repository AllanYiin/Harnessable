import json

from harnessable import HarnessProject, JsonlTraceExporter, LocalProjectStoreAdapter, OpenTelemetryStyleTraceExporter
from harnessable.events import EventType, HarnessEvent
from harnessable.observability import TraceRecord


def test_jsonl_trace_exporter_writes_sanitized_records(tmp_path):
    event = HarnessEvent(
        event_id="evt_1",
        run_id="run_1",
        event_type=EventType.TOOL_CALL_REQUESTED,
        payload={"token": "secret-token", "safe": "kept"},
        metadata={"gateway_call_id": "call_1"},
    )
    records = [{"event": event.to_dict(), "decision": {"effect": "ALLOW"}, "token": "secret-token"}]
    target = tmp_path / "trace.jsonl"

    JsonlTraceExporter().write(records, target)

    lines = target.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    exported = json.loads(lines[0])
    assert exported["event.event_id"] == "evt_1"
    assert exported["decision"]["effect"] == "ALLOW"
    assert "secret-token" not in lines[0]


def test_otel_style_exporter_emits_resource_spans():
    records = [
        TraceRecord(
            "gateway.call",
            {
                "event_id": "evt_1",
                "run_id": "run_1",
                "event_type": "MODEL_CALL_REQUESTED",
                "timestamp": "2026-06-14T00:00:00+00:00",
                "metadata": {"usage": {"input_tokens": 3}},
            },
        )
    ]

    batch = OpenTelemetryStyleTraceExporter(service_name="harnessable-test").export(records)
    payload = batch.records[0]

    resource_span = payload["resourceSpans"][0]
    assert resource_span["resource"]["attributes"][0]["value"]["stringValue"] == "harnessable-test"
    span = resource_span["scopeSpans"][0]["spans"][0]
    assert span["name"] == "MODEL_CALL_REQUESTED"
    assert len(span["traceId"]) == 32
    assert len(span["spanId"]) == 16


def test_local_project_store_adapter_migration_dry_run_is_read_only(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Demo")
    adapter = LocalProjectStoreAdapter(project.path)

    report = adapter.dry_run_migration("0.2.0")
    manifest_after = adapter.read_manifest()

    assert report.migration_required is True
    assert report.current_version == "0.1.0"
    assert report.target_version == "0.2.0"
    assert manifest_after["version"] == "0.1.0"
    assert "dry run only" in report.limitations[0]
