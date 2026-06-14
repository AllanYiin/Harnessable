from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from harnessable.project import HarnessProject

_REDACTED = "[REDACTED]"
_SENSITIVE_KEY_PARTS = ("secret", "token", "password", "api_key", "apikey", "authorization")


@dataclass(slots=True)
class AuditPackage:
    run_id: str
    package_id: str = field(default_factory=lambda: f"audit_{uuid4().hex}")
    schema_version: str = "1"
    project_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_trace_refs: list[str] = field(default_factory=list)
    event_refs: list[str] = field(default_factory=list)
    decision_refs: list[str] = field(default_factory=list)
    gateway_call_refs: list[str] = field(default_factory=list)
    approval_refs: list[str] = field(default_factory=list)
    artifact_refs: list[str] = field(default_factory=list)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    eval_refs: list[str] = field(default_factory=list)
    replay_refs: list[str] = field(default_factory=list)
    policy_pack_refs: list[str] = field(default_factory=list)
    lineage_refs: list[str] = field(default_factory=list)
    records: list[dict[str, Any]] = field(default_factory=list)
    redaction_summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    integrity_hash: str = ""

    def to_dict(self, include_integrity: bool = True) -> dict[str, Any]:
        data = {
            "schema_version": self.schema_version,
            "package_id": self.package_id,
            "run_id": self.run_id,
            "project_id": self.project_id or "unknown",
            "created_at": self.created_at,
            "source_trace_refs": list(self.source_trace_refs),
            "event_refs": list(self.event_refs),
            "decision_refs": list(self.decision_refs),
            "gateway_call_refs": list(self.gateway_call_refs),
            "approval_refs": list(self.approval_refs),
            "artifact_refs": list(self.artifact_refs),
            "artifact_hashes": dict(self.artifact_hashes),
            "eval_refs": list(self.eval_refs),
            "replay_refs": list(self.replay_refs),
            "policy_pack_refs": list(self.policy_pack_refs),
            "lineage_refs": list(self.lineage_refs),
            "records": list(self.records),
            "redaction_summary": dict(self.redaction_summary),
            "warnings": list(self.warnings),
        }
        if include_integrity:
            data["integrity_hash"] = self.integrity_hash
        return data

    def compute_integrity_hash(self) -> str:
        canonical = json.dumps(self.to_dict(include_integrity=False), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def seal(self) -> "AuditPackage":
        self.integrity_hash = self.compute_integrity_hash()
        return self


class AuditPackageExporter:
    def __init__(self, project: HarnessProject) -> None:
        self.project = project

    def export_run(
        self,
        run_id: str,
        *,
        eval_refs: list[str] | None = None,
        replay_refs: list[str] | None = None,
        policy_pack_refs: list[str] | None = None,
        lineage_refs: list[str] | None = None,
        created_at: str | None = None,
        package_id: str | None = None,
    ) -> AuditPackage:
        raw_records = self.project.state.read_events(run_id)
        redacted_records, redaction_summary = redact_value(raw_records)
        warnings: list[str] = []
        if not raw_records:
            warnings.append("no_run_records")

        event_refs = _collect_event_refs(raw_records)
        decision_refs = _collect_decision_refs(raw_records)
        gateway_call_refs = _collect_gateway_call_refs(raw_records)
        approval_refs = sorted(_collect_values(raw_records, {"approval_id", "approval_ref", "approval_refs"}))
        artifact_refs = sorted(_collect_artifact_refs(raw_records))
        collected_lineage_refs = sorted(_collect_values(raw_records, {"lineage_id", "lineage_ref", "lineage_refs"}))
        artifact_hashes = self._artifact_hashes(artifact_refs, warnings)

        package = AuditPackage(
            package_id=package_id or f"audit_{uuid4().hex}",
            run_id=run_id,
            project_id=self.project.manifest.name or "unknown",
            created_at=created_at or datetime.now(timezone.utc).isoformat(),
            source_trace_refs=[f"runs/{run_id}.jsonl"] if raw_records else [],
            event_refs=event_refs or ["unknown"],
            decision_refs=decision_refs or ["unknown"],
            gateway_call_refs=gateway_call_refs,
            approval_refs=approval_refs,
            artifact_refs=artifact_refs,
            artifact_hashes=artifact_hashes,
            eval_refs=eval_refs or [],
            replay_refs=replay_refs or [],
            policy_pack_refs=policy_pack_refs or [],
            lineage_refs=sorted(set([*(lineage_refs or []), *collected_lineage_refs])),
            records=redacted_records,
            redaction_summary=redaction_summary,
            warnings=warnings,
        )
        return package.seal()

    def _artifact_hashes(self, artifact_refs: list[str], warnings: list[str]) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for artifact_ref in artifact_refs:
            artifact_id = _artifact_id_from_ref(artifact_ref)
            if not artifact_id:
                continue
            path = self.project.artifacts.root / f"{artifact_id}.json"
            if not path.exists():
                warnings.append(f"artifact_missing:{artifact_ref}")
                continue
            hashes[artifact_ref] = _sha256_file(path)
        return hashes


def redact_value(value: Any, path: str = "") -> tuple[Any, dict[str, Any]]:
    redacted_paths: list[str] = []

    def visit(node: Any, current_path: str) -> Any:
        if isinstance(node, dict):
            result = {}
            for key, child in node.items():
                child_path = f"{current_path}.{key}" if current_path else str(key)
                if _is_sensitive_key(str(key)):
                    redacted_paths.append(child_path)
                    result[key] = _REDACTED
                else:
                    result[key] = visit(child, child_path)
            return result
        if isinstance(node, list):
            return [visit(child, f"{current_path}[{index}]") for index, child in enumerate(node)]
        return node

    redacted = visit(value, path)
    return redacted, {"redacted_count": len(redacted_paths), "redacted_paths": redacted_paths}


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _collect_event_refs(records: list[dict[str, Any]]) -> list[str]:
    refs = []
    for record in records:
        event = record.get("event") or {}
        event_id = event.get("event_id")
        if event_id:
            refs.append(str(event_id))
    return refs


def _collect_decision_refs(records: list[dict[str, Any]]) -> list[str]:
    refs = []
    for record in records:
        event = record.get("event") or {}
        decision = record.get("decision") or {}
        decision_id = decision.get("event_id") or event.get("event_id")
        if decision_id:
            refs.append(str(decision_id))
    return refs


def _collect_gateway_call_refs(records: list[dict[str, Any]]) -> list[str]:
    refs = []
    gateway_markers = ("MODEL_", "TOOL_", "MEMORY_", "RESOURCE_", "AGENT_", "PUBLICATION_", "CONTEXT_")
    for record in records:
        event = record.get("event") or {}
        event_type = str(event.get("event_type") or "")
        event_id = event.get("event_id")
        if event_id and any(event_type.startswith(marker) for marker in gateway_markers):
            refs.append(str(event_id))
    return refs


def _collect_artifact_refs(records: list[dict[str, Any]]) -> set[str]:
    refs = set(_collect_values(records, {"artifact_id", "artifact_ref", "artifact_refs", "execution_evidence_refs"}))
    for evidence_ref in _collect_values(records, {"evidence_ref", "evidence_refs"}):
        if str(evidence_ref).startswith("artifact://"):
            refs.add(str(evidence_ref))
    return refs


def _collect_values(value: Any, keys: set[str]) -> set[str]:
    values: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key in keys:
                    if isinstance(child, list):
                        values.update(str(item) for item in child if item not in (None, ""))
                    elif child not in (None, ""):
                        values.add(str(child))
                visit(child)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(value)
    return values


def _artifact_id_from_ref(artifact_ref: str) -> str | None:
    if artifact_ref.startswith("artifact://"):
        return artifact_ref[len("artifact://") :].split("#", 1)[0]
    if artifact_ref.startswith("artifact_"):
        return artifact_ref
    return None


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
