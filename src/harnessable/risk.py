from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harnessable.core.serialization import to_plain


RISK_SCHEMA_VERSION = "1"


@dataclass(slots=True)
class RiskFinding:
    """Structured finding from an external scanner or review system."""

    type: str
    schema_version: str = RISK_SCHEMA_VERSION
    severity: str = "medium"
    message: str = ""
    source: str | None = None
    evidence_ref: str | None = None
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskFinding":
        payload = dict(data)
        return cls(
            type=str(payload["type"]),
            schema_version=str(payload.get("schema_version") or RISK_SCHEMA_VERSION),
            severity=str(payload.get("severity") or "medium"),
            message=str(payload.get("message") or ""),
            source=payload.get("source"),
            evidence_ref=payload.get("evidence_ref"),
            confidence=float(payload.get("confidence", 1.0)),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(slots=True)
class SimilarityFinding:
    """Typed contract for external similarity or near-duplicate scanner matches."""

    matched_asset_ref: str
    similarity_score: float
    schema_version: str = RISK_SCHEMA_VERSION
    severity: str = "high"
    message: str = "Asset similarity requires rights or originality review."
    source: str | None = "similarity_scanner"
    evidence_ref: str | None = None
    confidence: float = 1.0
    license_status: str | None = None
    transform_type: str | None = None
    asset_region: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_risk_finding(self) -> RiskFinding:
        metadata = {
            **self.metadata,
            "matched_asset_ref": self.matched_asset_ref,
            "similarity_score": self.similarity_score,
            "license_status": self.license_status,
            "transform_type": self.transform_type,
            "asset_region": self.asset_region,
        }
        return RiskFinding(
            type="similarity.match",
            schema_version=self.schema_version,
            severity=self.severity,
            message=self.message,
            source=self.source,
            evidence_ref=self.evidence_ref,
            confidence=self.confidence,
            metadata={key: value for key, value in metadata.items() if value not in (None, "", [], {})},
        )

    def to_dict(self) -> dict[str, Any]:
        return self.to_risk_finding().to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimilarityFinding":
        payload = dict(data)
        metadata = dict(payload.get("metadata") or {})
        return cls(
            matched_asset_ref=metadata.get("matched_asset_ref") or payload["matched_asset_ref"],
            similarity_score=float(metadata.get("similarity_score", payload.get("similarity_score"))),
            schema_version=str(payload.get("schema_version") or RISK_SCHEMA_VERSION),
            severity=payload.get("severity", "high"),
            message=payload.get("message", "Asset similarity requires rights or originality review."),
            source=payload.get("source", "similarity_scanner"),
            evidence_ref=payload.get("evidence_ref"),
            confidence=float(payload.get("confidence", 1.0)),
            license_status=metadata.get("license_status") or payload.get("license_status"),
            transform_type=metadata.get("transform_type") or payload.get("transform_type"),
            asset_region=metadata.get("asset_region") or payload.get("asset_region") or {},
            metadata={key: value for key, value in metadata.items() if key not in {"matched_asset_ref", "similarity_score", "license_status", "transform_type", "asset_region"}},
        )


@dataclass(slots=True)
class ProvenanceFinding:
    """Typed contract for external provenance, attribution, and rights scanner findings."""

    source_type: str
    schema_version: str = RISK_SCHEMA_VERSION
    rights_status: str = "unknown"
    required_rights: list[str] = field(default_factory=list)
    severity: str = "high"
    message: str = "Asset provenance or rights status requires review."
    source: str | None = "provenance_scanner"
    evidence_ref: str | None = None
    confidence: float = 1.0
    source_ref: str | None = None
    attribution: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_risk_finding(self) -> RiskFinding:
        metadata = {
            **self.metadata,
            "source_type": self.source_type,
            "rights_status": self.rights_status,
            "required_rights": self.required_rights,
            "source_ref": self.source_ref,
            "attribution": self.attribution,
        }
        return RiskFinding(
            type="provenance.review",
            schema_version=self.schema_version,
            severity=self.severity,
            message=self.message,
            source=self.source,
            evidence_ref=self.evidence_ref,
            confidence=self.confidence,
            metadata={key: value for key, value in metadata.items() if value not in (None, "", [], {})},
        )

    def to_dict(self) -> dict[str, Any]:
        return self.to_risk_finding().to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProvenanceFinding":
        payload = dict(data)
        metadata = dict(payload.get("metadata") or {})
        return cls(
            source_type=metadata.get("source_type") or payload["source_type"],
            schema_version=str(payload.get("schema_version") or RISK_SCHEMA_VERSION),
            rights_status=metadata.get("rights_status") or payload.get("rights_status", "unknown"),
            required_rights=list(metadata.get("required_rights") or payload.get("required_rights") or []),
            severity=payload.get("severity", "high"),
            message=payload.get("message", "Asset provenance or rights status requires review."),
            source=payload.get("source", "provenance_scanner"),
            evidence_ref=payload.get("evidence_ref"),
            confidence=float(payload.get("confidence", 1.0)),
            source_ref=metadata.get("source_ref") or payload.get("source_ref"),
            attribution=metadata.get("attribution") or payload.get("attribution"),
            metadata={key: value for key, value in metadata.items() if key not in {"source_type", "rights_status", "required_rights", "source_ref", "attribution"}},
        )


@dataclass(slots=True)
class ScannerResult:
    """Adapter contract for OCR, CV, claim, provenance, or rights scanners."""

    scanner_id: str
    schema_version: str = RISK_SCHEMA_VERSION
    status: str = "completed"
    findings: list[RiskFinding | SimilarityFinding | ProvenanceFinding | dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scanner_id": self.scanner_id,
            "status": self.status,
            "findings": [_finding_to_dict(finding) for finding in self.findings],
            "metadata": to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScannerResult":
        payload = dict(data)
        payload["findings"] = [
            finding if isinstance(finding, RiskFinding) else _finding_from_dict(finding)
            for finding in payload.get("findings", [])
        ]
        return cls(
            scanner_id=str(payload["scanner_id"]),
            schema_version=str(payload.get("schema_version") or RISK_SCHEMA_VERSION),
            status=str(payload.get("status") or "completed"),
            findings=payload["findings"],
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(slots=True)
class RiskContext:
    schema_version: str = RISK_SCHEMA_VERSION
    jurisdiction: str | None = None
    market: str | None = None
    locale: str | None = None
    release_at: str | None = None
    publish_window: str | dict[str, Any] | None = None
    audience: str | list[str] | None = None
    channel: str | None = None
    intent: str | None = None
    campaign_id: str | None = None
    asset_kind: str | None = None
    asset_hash: str | None = None
    genai_trace_id: str | None = None
    artifact_refs: list[str] = field(default_factory=list)
    ai_generated: bool | None = None
    claims: list[dict[str, Any]] = field(default_factory=list)
    offers: list[dict[str, Any]] = field(default_factory=list)
    rights: dict[str, Any] = field(default_factory=dict)
    scanner_results: list[ScannerResult | dict[str, Any]] = field(default_factory=list)
    scanner_coverage: dict[str, Any] = field(default_factory=dict)
    rollback_plan: dict[str, Any] = field(default_factory=dict)
    precedent_refs: list[str] = field(default_factory=list)
    known_constraints: dict[str, Any] = field(default_factory=dict)
    review_route: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = to_plain(self)
        payload["scanner_results"] = [
            result.to_dict() if isinstance(result, ScannerResult) else ScannerResult.from_dict(result).to_dict()
            for result in self.scanner_results
        ]
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskContext":
        payload = dict(data)
        payload["scanner_results"] = [
            result if isinstance(result, ScannerResult) else ScannerResult.from_dict(result)
            for result in payload.get("scanner_results", [])
        ]
        payload["schema_version"] = str(payload.get("schema_version") or RISK_SCHEMA_VERSION)
        return cls(**payload)


def _finding_to_dict(finding: RiskFinding | SimilarityFinding | ProvenanceFinding | dict[str, Any]) -> dict[str, Any]:
    if isinstance(finding, dict):
        return to_plain(finding)
    if isinstance(finding, (SimilarityFinding, ProvenanceFinding)):
        return finding.to_dict()
    return finding.to_dict()


def _finding_from_dict(data: dict[str, Any]) -> RiskFinding:
    finding_type = str(data.get("type") or "")
    if finding_type.startswith("similarity.") or "matched_asset_ref" in data:
        return SimilarityFinding.from_dict(data).to_risk_finding()
    if finding_type.startswith("provenance.") or "source_type" in data:
        return ProvenanceFinding.from_dict(data).to_risk_finding()
    return RiskFinding.from_dict(data)
