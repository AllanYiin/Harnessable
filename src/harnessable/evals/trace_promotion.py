from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

_REDACTED = "[REDACTED]"
_SENSITIVE_KEY_PARTS = ("secret", "token", "password", "api_key", "apikey", "authorization")

@dataclass(slots=True)
class TracePromotionPreview:
    preview_id: str
    source_run_id: str
    source_hash: str
    candidate_cases: list[dict[str, Any]]
    redaction_summary: dict[str, Any] = field(default_factory=dict)
    policy_versions: dict[str, Any] = field(default_factory=dict)
    expected_effects: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "source_run_id": self.source_run_id,
            "source_hash": self.source_hash,
            "candidate_cases": list(self.candidate_cases),
            "redaction_summary": dict(self.redaction_summary),
            "policy_versions": dict(self.policy_versions),
            "expected_effects": list(self.expected_effects),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TracePromotionPreview":
        return cls(**dict(data))


@dataclass(slots=True)
class TracePromotionApplyResult:
    preview_id: str
    applied: bool
    case_paths: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "applied": self.applied,
            "case_paths": list(self.case_paths),
            "errors": list(self.errors),
        }


@dataclass(slots=True)
class RolloutGateReport:
    report_id: str
    baseline_ref: str
    candidate_ref: str
    passed: bool
    changed_decisions: list[dict[str, Any]] = field(default_factory=list)
    blocked_regressions: list[dict[str, Any]] = field(default_factory=list)
    shadow_decisions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "baseline_ref": self.baseline_ref,
            "candidate_ref": self.candidate_ref,
            "pass": self.passed,
            "changed_decisions": list(self.changed_decisions),
            "blocked_regressions": list(self.blocked_regressions),
            "shadow_decisions": list(self.shadow_decisions),
        }

    @classmethod
    def from_replay_diff(cls, baseline_ref: str, candidate_ref: str, diff: dict[str, Any], report_id: str | None = None) -> "RolloutGateReport":
        changed = []
        blocked = []
        shadow = []
        baseline = diff.get("baseline_decisions") or []
        decisions = diff.get("decisions") or []
        for index, decision in enumerate(decisions):
            baseline_decision = baseline[index] if index < len(baseline) else {}
            if decision != baseline_decision:
                change = {"index": index, "baseline": baseline_decision, "candidate": decision}
                changed.append(change)
                if decision.get("effect") in {"BLOCK", "ABORT", "FAIL_SAFE"} and baseline_decision.get("effect") not in {"BLOCK", "ABORT", "FAIL_SAFE"}:
                    blocked.append(change)
            for contributing in decision.get("contributing_decisions") or []:
                if contributing.get("shadow"):
                    shadow.append(contributing)
        return cls(
            report_id=report_id or f"rollout_{uuid4().hex}",
            baseline_ref=baseline_ref,
            candidate_ref=candidate_ref,
            passed=not changed,
            changed_decisions=changed,
            blocked_regressions=blocked,
            shadow_decisions=shadow,
        )


class TracePromotionStore:
    def __init__(self, project_path: str | Path) -> None:
        self.project_path = Path(project_path)
        self.previews_path = self.project_path / "imports" / "trace_promotions"
        self.evals_path = self.project_path / "evals"
        self.previews_path.mkdir(parents=True, exist_ok=True)
        self.evals_path.mkdir(parents=True, exist_ok=True)

    def preview(self, run_id: str, records: list[dict[str, Any]]) -> TracePromotionPreview:
        source_hash = _hash_records(records)
        redacted_records, redaction_summary = redact_value(records)
        warnings: list[str] = []
        if not records:
            warnings.append("no_run_records")
        candidate_cases = []
        expected_effects = []
        for record in redacted_records:
            event = record.get("event") or {}
            decision = record.get("decision") or {}
            event_id = str(event.get("event_id") or "unknown_event")
            effect = str(decision.get("effect") or "ALLOW")
            expected_effects.append(effect)
            candidate_cases.append(
                {
                    "schema_version": "1",
                    "id": _case_id(run_id, event_id),
                    "event": event,
                    "expected_effect": effect,
                    "metadata": {
                        "source_run_id": run_id,
                        "source_event_id": event_id,
                        "source_hash": source_hash,
                        "promoted_from_trace": True,
                    },
                }
            )
        preview = TracePromotionPreview(
            preview_id=f"trace_preview_{source_hash[:16]}",
            source_run_id=run_id,
            source_hash=source_hash,
            candidate_cases=candidate_cases,
            redaction_summary=redaction_summary,
            policy_versions={"trace_promotion": "1"},
            expected_effects=expected_effects,
            warnings=warnings,
        )
        self._path(preview.preview_id).write_text(json.dumps(preview.to_dict(), indent=2), encoding="utf-8")
        return preview

    def get(self, preview_id: str) -> TracePromotionPreview:
        return TracePromotionPreview.from_dict(json.loads(self._path(preview_id).read_text(encoding="utf-8")))

    def apply(self, preview_id: str, current_records: list[dict[str, Any]]) -> TracePromotionApplyResult:
        preview = self.get(preview_id)
        if _hash_records(current_records) != preview.source_hash:
            return TracePromotionApplyResult(
                preview_id=preview_id,
                applied=False,
                errors=["source run changed after preview; create a new preview before apply"],
            )
        if not preview.candidate_cases:
            return TracePromotionApplyResult(preview_id=preview_id, applied=False, errors=["preview has no candidate cases"])
        paths = []
        for case in preview.candidate_cases:
            target = self.evals_path / f"{_safe_filename(str(case['id']))}.json"
            target.write_text(json.dumps(case, indent=2), encoding="utf-8")
            paths.append(str(target))
        return TracePromotionApplyResult(preview_id=preview_id, applied=True, case_paths=paths)

    def _path(self, preview_id: str) -> Path:
        return self.previews_path / f"{preview_id}.json"


def _hash_records(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def _case_id(run_id: str, event_id: str) -> str:
    return _safe_filename(f"{run_id}_{event_id}")


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "case"
