from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .tracing import TraceRecord

_SENSITIVE_KEYS = {"payload", "content", "secret", "token", "password", "api_key", "authorization"}


@dataclass(frozen=True)
class ObservabilityExportBatch:
    exporter_id: str
    schema_version: str = "1"
    records: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "exporter_id": self.exporter_id,
            "schema_version": self.schema_version,
            "records": list(self.records),
            "warnings": list(self.warnings),
        }


class ObservabilityExporter(Protocol):
    exporter_id: str

    def export(self, records: list[dict[str, Any]] | list[TraceRecord]) -> ObservabilityExportBatch: ...


@dataclass(frozen=True)
class JsonlTraceExporter:
    exporter_id: str = "jsonl.trace"

    def export(self, records: list[dict[str, Any]] | list[TraceRecord]) -> ObservabilityExportBatch:
        return ObservabilityExportBatch(
            exporter_id=self.exporter_id,
            records=tuple(_normalize_record(record) for record in records),
        )

    def write(self, records: list[dict[str, Any]] | list[TraceRecord], target_path: str | Path) -> Path:
        batch = self.export(records)
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            for record in batch.records:
                fh.write(json.dumps(record, sort_keys=True) + "\n")
        return target


@dataclass(frozen=True)
class OpenTelemetryStyleTraceExporter:
    service_name: str = "harnessable"
    instrumentation_scope: str = "harnessable.observability"
    exporter_id: str = "otel.style.trace"

    def export(self, records: list[dict[str, Any]] | list[TraceRecord]) -> ObservabilityExportBatch:
        spans = [_record_to_span(_normalize_record(record)) for record in records]
        payload = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            _attribute("service.name", self.service_name),
                            _attribute("telemetry.sdk.name", "harnessable"),
                        ]
                    },
                    "scopeSpans": [
                        {
                            "scope": {"name": self.instrumentation_scope},
                            "spans": spans,
                        }
                    ],
                }
            ]
        }
        return ObservabilityExportBatch(exporter_id=self.exporter_id, records=(payload,))


def _normalize_record(record: dict[str, Any] | TraceRecord) -> dict[str, Any]:
    if isinstance(record, TraceRecord):
        payload = {"kind": record.kind, **record.payload}
    else:
        payload = dict(record)
    event = payload.get("event")
    if isinstance(event, dict):
        normalized = {**payload, **{f"event.{key}": value for key, value in event.items() if key != "payload"}}
    else:
        normalized = payload
    return _sanitize(normalized)


def _record_to_span(record: dict[str, Any]) -> dict[str, Any]:
    event_id = str(record.get("event.event_id") or record.get("event_id") or record.get("kind") or "record")
    trace_id = str(record.get("event.trace_id") or record.get("trace_id") or record.get("event.run_id") or record.get("run_id") or event_id)
    name = str(record.get("event.event_type") or record.get("event_type") or record.get("kind") or "harnessable.record")
    timestamp = str(record.get("event.timestamp") or record.get("timestamp") or _now_iso())
    attributes = [_attribute(key, value) for key, value in sorted(record.items()) if key not in {"event.payload", "payload", "content"}]
    return {
        "traceId": _hex_id(trace_id, 32),
        "spanId": _hex_id(event_id, 16),
        "parentSpanId": _hex_id(str(record["event.parent_event_id"]), 16) if record.get("event.parent_event_id") else None,
        "name": name,
        "kind": "SPAN_KIND_INTERNAL",
        "startTimeUnixNano": _iso_to_unix_nano(timestamp),
        "endTimeUnixNano": _iso_to_unix_nano(timestamp),
        "attributes": attributes,
    }


def _attribute(key: str, value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        typed = {"boolValue": value}
    elif isinstance(value, int):
        typed = {"intValue": value}
    elif isinstance(value, float):
        typed = {"doubleValue": value}
    else:
        typed = {"stringValue": json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)}
    return {"key": key, "value": typed}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize(child) for key, child in value.items() if key.lower() not in _SENSITIVE_KEYS}
    if isinstance(value, list):
        return [_sanitize(child) for child in value]
    return value


def _hex_id(value: str, length: int) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_to_unix_nano(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = datetime.now(timezone.utc)
    return str(int(parsed.timestamp() * 1_000_000_000))
