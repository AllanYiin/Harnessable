from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvidenceMappingEntry:
    framework: str
    control_id: str
    supports_evidence_for: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework": self.framework,
            "control_id": self.control_id,
            "supports_evidence_for": self.supports_evidence_for,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class ComplianceSupportExport:
    framework: str
    schema_version: str
    entries: tuple[EvidenceMappingEntry, ...]
    limitations: tuple[str, ...]
    disclaimer: str = "Supports evidence preparation only; not legal advice, certification, or a compliance guarantee."

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework": self.framework,
            "schema_version": self.schema_version,
            "entries": [entry.to_dict() for entry in self.entries],
            "limitations": list(self.limitations),
            "disclaimer": self.disclaimer,
        }


def build_nist_ai_rmf_export(evidence_refs: list[str] | tuple[str, ...]) -> ComplianceSupportExport:
    refs = tuple(evidence_refs)
    return ComplianceSupportExport(
        framework="NIST AI RMF",
        schema_version="1",
        entries=(
            EvidenceMappingEntry("NIST AI RMF", "govern", "documented governance policies and accountability evidence", refs),
            EvidenceMappingEntry("NIST AI RMF", "map", "context, stakeholder, and risk source evidence", refs),
            EvidenceMappingEntry("NIST AI RMF", "measure", "eval, replay, trace, and benchmark evidence", refs),
            EvidenceMappingEntry("NIST AI RMF", "manage", "approval, mitigation, rollout, and monitoring evidence", refs),
        ),
        limitations=("framework mapping is evidence support only", "human review is required before external use"),
    )


def build_iso42001_support_export(evidence_refs: list[str] | tuple[str, ...]) -> ComplianceSupportExport:
    refs = tuple(evidence_refs)
    return ComplianceSupportExport(
        framework="ISO/IEC 42001",
        schema_version="1",
        entries=(
            EvidenceMappingEntry("ISO/IEC 42001", "policy", "AI management-system policy evidence", refs),
            EvidenceMappingEntry("ISO/IEC 42001", "risk_treatment", "risk assessment and treatment evidence", refs),
            EvidenceMappingEntry("ISO/IEC 42001", "monitoring", "trace, audit, eval, and continual improvement evidence", refs),
        ),
        limitations=("does not certify an AI management system", "organizational controls must be assessed outside the SDK"),
    )


def build_eu_ai_act_support_export(evidence_refs: list[str] | tuple[str, ...]) -> ComplianceSupportExport:
    refs = tuple(evidence_refs)
    return ComplianceSupportExport(
        framework="EU AI Act high-risk support checklist",
        schema_version="1",
        entries=(
            EvidenceMappingEntry("EU AI Act", "risk_management", "risk-management evidence for AI system workflows", refs),
            EvidenceMappingEntry("EU AI Act", "logging", "logging and traceability evidence", refs),
            EvidenceMappingEntry("EU AI Act", "human_oversight", "approval and operator oversight evidence", refs),
            EvidenceMappingEntry("EU AI Act", "technical_documentation", "technical documentation and limitation evidence", refs),
        ),
        limitations=("not legal advice", "system classification and legal obligations require qualified review"),
    )


@dataclass(frozen=True)
class VerticalHarnessPack:
    pack_id: str
    name: str
    profile: str
    schema_version: str = "1"
    supports_evidence_for: tuple[str, ...] = field(default_factory=tuple)
    default_rules: tuple[str, ...] = field(default_factory=tuple)
    default_capabilities: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "pack_id": self.pack_id,
            "name": self.name,
            "profile": self.profile,
            "supports_evidence_for": list(self.supports_evidence_for),
            "default_rules": list(self.default_rules),
            "default_capabilities": list(self.default_capabilities),
            "limitations": list(self.limitations),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VerticalHarnessPack":
        data = dict(payload)
        for key in ("supports_evidence_for", "default_rules", "default_capabilities", "limitations"):
            data[key] = tuple(data.get(key) or ())
        return cls(**data)


@dataclass(frozen=True)
class VerticalPackPreview:
    preview_id: str
    pack: VerticalHarnessPack
    source_hash: str
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "pack": self.pack.to_dict(),
            "source_hash": self.source_hash,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class VerticalPackApplyResult:
    preview_id: str
    applied: bool
    pack_id: str
    path: str
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "preview_id": self.preview_id,
            "applied": self.applied,
            "pack_id": self.pack_id,
            "path": self.path,
            "warnings": list(self.warnings),
        }


class VerticalPackStore:
    def __init__(self, project_path: str | Path) -> None:
        self.root = Path(project_path)
        self.previews = self.root / "pack_previews"
        self.packs = self.root / "packs"
        self.previews.mkdir(parents=True, exist_ok=True)
        self.packs.mkdir(parents=True, exist_ok=True)

    def preview(self, pack: VerticalHarnessPack) -> VerticalPackPreview:
        warnings = tuple(_pack_warnings(pack))
        source_hash = _hash_dict(pack.to_dict())
        preview = VerticalPackPreview(preview_id=f"pack_preview_{source_hash[:12]}", pack=pack, source_hash=source_hash, warnings=warnings)
        (self.previews / f"{preview.preview_id}.json").write_text(json.dumps(preview.to_dict(), indent=2), encoding="utf-8")
        return preview

    def apply(self, preview_id: str) -> VerticalPackApplyResult:
        preview_path = self.previews / f"{preview_id}.json"
        payload = json.loads(preview_path.read_text(encoding="utf-8"))
        pack = VerticalHarnessPack.from_dict(payload["pack"])
        source_hash = _hash_dict(pack.to_dict())
        if source_hash != payload["source_hash"]:
            raise ValueError("vertical pack preview is stale")
        target = self.packs / f"{pack.pack_id}.json"
        target.write_text(json.dumps(pack.to_dict(), indent=2), encoding="utf-8")
        return VerticalPackApplyResult(preview_id=preview_id, applied=True, pack_id=pack.pack_id, path=str(target), warnings=tuple(payload.get("warnings") or ()))


def builtin_vertical_packs() -> dict[str, VerticalHarnessPack]:
    return {
        "coding": VerticalHarnessPack(
            pack_id="coding",
            name="Coding Agent Harness Pack",
            profile="coding",
            supports_evidence_for=("code execution review", "artifact update governance", "tool permission review"),
            default_rules=("code_execution.block_secret_or_broad_write.v1",),
            default_capabilities=("code_execution", "artifact_review", "trace_replay"),
            limitations=("requires project-specific sandbox and repository policy review",),
        ),
        "research": VerticalHarnessPack(
            pack_id="research",
            name="Research Agent Harness Pack",
            profile="research",
            supports_evidence_for=("source traceability", "claim evidence review", "lineage envelope review"),
            default_rules=("lineage.required_sources.v1",),
            default_capabilities=("lineage_envelope", "audit_package", "trace_promotion"),
            limitations=("does not validate source truth by itself",),
        ),
        "ops": VerticalHarnessPack(
            pack_id="ops",
            name="Ops Agent Harness Pack",
            profile="ops",
            supports_evidence_for=("approval routing", "fallback safety", "deployment audit evidence"),
            default_rules=("fallback.no_authority_broadening.v1",),
            default_capabilities=("approval_queue", "fallback_graph", "observability_export"),
            limitations=("requires environment-specific incident and escalation policy",),
        ),
    }


def _pack_warnings(pack: VerticalHarnessPack) -> list[str]:
    warnings = []
    if not pack.supports_evidence_for:
        warnings.append("missing_supports_evidence_for")
    forbidden = " ".join([pack.name, *pack.supports_evidence_for, *pack.limitations]).lower()
    for phrase in ("certified", "guaranteed compliant", "legal compliance"):
        if phrase in forbidden:
            warnings.append("claim_exceeds_evidence")
    return warnings


def _hash_dict(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
