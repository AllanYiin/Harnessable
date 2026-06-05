from __future__ import annotations

import re
from dataclasses import is_dataclass
from typing import Any

from harnessable.core.serialization import to_plain
from harnessable.events import HarnessEvent

from .base import HarnessDetector
from .results import DetectionOutcome, DetectionResult


AUDIT_REASON_KEYS = [
    "risk_hypotheses",
    "missing_context",
    "affected_stakeholders",
    "misread_paths",
    "required_reviewers",
    "release_constraints",
    "asset_hash",
    "scanner_coverage_gaps",
    "scanner_findings",
    "similarity_matches",
    "provenance_findings",
    "claim_gaps",
    "offer_disclosure_gaps",
    "provenance_gaps",
    "override_expiry",
    "rollback_constraints",
    "incident_links",
]


class ContextGapDetector(HarnessDetector):
    detector_id = "context_gap_detector"

    def __init__(self, required_fields: list[str] | None = None) -> None:
        self.required_fields = required_fields or [
            "jurisdiction",
            "locale",
            "release_at",
            "audience",
            "channel",
            "intent",
            "artifact_refs",
            "ai_generated",
        ]

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        context = _risk_context(event)
        missing = [field for field in self.required_fields if _missing(_lookup(context, field))]
        review_route = _lookup(context, "review_route") or {}
        if _missing(_lookup(review_route, "approval_reason")):
            missing.append("review_route.approval_reason")
        if missing:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                reason=_reason(
                    "CONTEXT_GAP",
                    missing_context=missing,
                    risk_hypotheses=["unknown contextual harm cannot be ruled out until release context is complete"],
                    required_reviewers=["owner"],
                    release_constraints=["complete risk context before external release"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("CONTEXT_COMPLETE"))


class StakeholderHarmDetector(HarnessDetector):
    detector_id = "stakeholder_harm_detector"

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        evidence = _risk_evidence(event)
        stakeholders = _lookup(evidence, "affected_stakeholders")
        if not _missing(stakeholders):
            return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("STAKEHOLDERS_REVIEWED"))
        return DetectionResult(
            DetectionOutcome.DETECTED,
            confidence=0.8,
            reason=_reason(
                "STAKEHOLDER_HARM_NOT_REVIEWED",
                affected_stakeholders=[
                    "target audience",
                    "people outside the intended audience",
                    "groups named or implied by the artifact",
                    "people connected to nearby public events or collective memory",
                ],
                risk_hypotheses=["the artifact may impose reputational, dignity, exclusion, or retraumatization harm on a group not represented in the brief"],
                required_reviewers=["content owner", "local/context reviewer"],
            ),
        )


class MisreadSimulator(HarnessDetector):
    detector_id = "misread_simulator"

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        evidence = _risk_evidence(event)
        if not _missing(_lookup(evidence, "misread_paths")):
            return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("MISREAD_PATHS_REVIEWED"))
        content = _content(event)
        paths = [
            "hostile framing: audience interprets the artifact as intentional mockery or endorsement",
            "trauma framing: audience maps wording, imagery, or timing onto public suffering",
            "political framing: audience treats the artifact as a partisan or ideological signal",
            "commercialization framing: audience sees the artifact as monetizing pain or identity",
            "translation or wordplay framing: ambiguity, homophones, or slogans shift meaning across locales",
        ]
        if _has_wordplay(content):
            paths.append("wordplay amplification: rhyme, pun, or sound effects make the risky interpretation more memorable")
        return DetectionResult(
            DetectionOutcome.DETECTED,
            confidence=0.75,
            reason=_reason(
                "MISREAD_PATHS_NOT_SIMULATED",
                misread_paths=paths,
                risk_hypotheses=["reasonable unintended interpretations have not been disproven"],
                required_reviewers=["content owner", "communications reviewer"],
            ),
        )


class PowerAsymmetryDetector(HarnessDetector):
    detector_id = "power_asymmetry_detector"

    _harm_terms = re.compile(
        r"\b(death|dead|kill|war|massacre|disaster|victim|refugee|minority|disabled|poverty|religion|race|ethnic|"
        r"protest|dictator|torture|trauma|memorial|mourning|violence|genocide|terror|colonial|slavery)\b",
        re.IGNORECASE,
    )
    _commercial_terms = re.compile(r"\b(sale|promo|campaign|discount|ad|advert|marketing|launch|buy|deal|brand)\b", re.IGNORECASE)

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        text = _content(event)
        intent = str(_lookup(_risk_context(event), "intent") or "")
        has_harm_frame = bool(self._harm_terms.search(text))
        commercial = bool(self._commercial_terms.search(text + " " + intent))
        if has_harm_frame and commercial:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                confidence=0.85,
                reason=_reason(
                    "POWER_ASYMMETRY_COMMERCIALIZATION_RISK",
                    risk_hypotheses=["commercial framing may trivialize suffering, identity, or unequal power relations"],
                    affected_stakeholders=["people connected to the referenced harm or identity", "local community", "brand frontline workers"],
                    required_reviewers=["legal reviewer", "CSR reviewer", "local/context reviewer"],
                    release_constraints=["remove commercial framing or require explicit cross-functional approval"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("POWER_ASYMMETRY_NOT_DETECTED"))


class ReleasePressureDetector(HarnessDetector):
    detector_id = "release_pressure_detector"

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        context = _risk_context(event)
        constraints = _lookup(context, "known_constraints") or {}
        review_route = _lookup(context, "review_route") or {}
        skipped = list(_lookup(review_route, "skipped_reviewers") or [])
        pressure = bool(_lookup(constraints, "fast_track")) or bool(skipped)
        if _lookup(constraints, "deadline_hours") is not None:
            pressure = pressure or float(_lookup(constraints, "deadline_hours")) < 24
        if pressure:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                confidence=0.8,
                reason=_reason(
                    "RELEASE_PRESSURE_DETECTED",
                    risk_hypotheses=["schedule pressure can align multiple process gaps and bypass contextual review"],
                    missing_context=[f"skipped:{role}" for role in skipped],
                    required_reviewers=skipped or ["release owner"],
                    release_constraints=["do not publish until skipped reviews are restored or explicitly counter-approved"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("NO_RELEASE_PRESSURE"))


class ClaimEvidenceDetector(HarnessDetector):
    detector_id = "claim_evidence_detector"

    regulated_types = {"health", "nutrition", "safety", "performance", "price", "price_comparison", "comparative"}

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        context = _risk_context(event)
        gaps: list[str] = []
        for index, claim in enumerate(_lookup(context, "claims") or []):
            claim_type = str(_lookup(claim, "type") or _lookup(claim, "category") or "").lower()
            requires_evidence = bool(_lookup(claim, "requires_evidence")) or claim_type in self.regulated_types
            evidence_id = _lookup(claim, "evidence_id") or _lookup(claim, "evidence_ref")
            if requires_evidence and _missing(evidence_id):
                label = _lookup(claim, "text") or _lookup(claim, "id") or f"claim[{index}]"
                gaps.append(str(label))
        if gaps:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                confidence=0.9,
                reason=_reason(
                    "CLAIM_EVIDENCE_MISSING",
                    claim_gaps=gaps,
                    risk_hypotheses=["regulated or comparative claims cannot be disproven without attached evidence"],
                    required_reviewers=["legal reviewer", "claims reviewer"],
                    release_constraints=["attach evidence_id or remove the claim before publication"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("CLAIMS_HAVE_EVIDENCE"))


class OfferDisclosureDetector(HarnessDetector):
    detector_id = "offer_disclosure_detector"

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        context = _risk_context(event)
        gaps: list[str] = []
        for index, offer in enumerate(_lookup(context, "offers") or []):
            subscription = _lookup(offer, "subscription") or {}
            disclosure = _lookup(offer, "disclosure") or {}
            precharge_notice = _lookup(offer, "precharge_notice") or _lookup(subscription, "precharge_notice") or {}
            has_freebie = bool(_lookup(offer, "contains_freebie") or _lookup(offer, "freebie"))
            auto_renew = bool(_lookup(subscription, "auto_renew") or _lookup(offer, "auto_renew"))
            if has_freebie and auto_renew:
                missing: list[str] = []
                if not _truthy(_lookup(disclosure, "above_the_fold")):
                    missing.append("disclosure.above_the_fold")
                if not _truthy(_lookup(precharge_notice, "enabled")):
                    missing.append("precharge_notice.enabled")
                if missing:
                    label = _lookup(offer, "id") or f"offer[{index}]"
                    gaps.append(f"{label}: {', '.join(missing)}")
        if gaps:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                confidence=0.9,
                reason=_reason(
                    "OFFER_DISCLOSURE_MISSING",
                    offer_disclosure_gaps=gaps,
                    risk_hypotheses=["free or discounted offers tied to auto-renewal can mislead users without prominent disclosure"],
                    required_reviewers=["consumer protection reviewer", "legal reviewer"],
                    release_constraints=["make renewal and pre-charge disclosure prominent before publication"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("OFFER_DISCLOSURES_COMPLETE"))


class ProvenanceMetadataDetector(HarnessDetector):
    detector_id = "provenance_metadata_detector"

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        context = _risk_context(event)
        rights = _lookup(context, "rights") or {}
        gaps: list[str] = []
        if _truthy(_lookup(context, "ai_generated")) and _missing(_lookup(context, "genai_trace_id")):
            gaps.append("genai_trace_id")
        requires_rights = any(
            _truthy(value)
            for value in (
                _lookup(rights, "requires_rights_review"),
                _lookup(rights, "uses_third_party_assets"),
                _lookup(rights, "uses_cultural_source"),
            )
        )
        if requires_rights:
            if _missing(_lookup(rights, "source_attribution")):
                gaps.append("rights.source_attribution")
            if _missing(_lookup(rights, "rights_token")) and _missing(_lookup(rights, "review_status")):
                gaps.append("rights.rights_token_or_review_status")
        if gaps:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                confidence=0.85,
                reason=_reason(
                    "PROVENANCE_METADATA_MISSING",
                    provenance_gaps=gaps,
                    risk_hypotheses=["asset origin, AI provenance, or rights status cannot be audited from the current context"],
                    required_reviewers=["rights reviewer", "content owner"],
                    release_constraints=["attach provenance and rights metadata before publication"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("PROVENANCE_METADATA_COMPLETE"))


class ScannerCoverageDetector(HarnessDetector):
    detector_id = "scanner_coverage_detector"

    default_required_by_asset_kind = {
        "ad_creative": ["ocr", "cv", "similarity", "provenance"],
        "image": ["ocr", "cv", "similarity", "provenance"],
        "landing_page": ["ocr", "similarity", "provenance"],
        "map": ["cv", "localization", "provenance"],
        "poster": ["ocr", "cv", "similarity", "provenance"],
        "product_design": ["similarity", "provenance", "rights"],
        "social_post": ["ocr", "cv", "similarity", "provenance"],
        "slogan": ["similarity", "provenance"],
        "text": ["similarity", "provenance"],
        "video": ["ocr", "cv", "asr", "similarity", "provenance"],
    }

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        context = _risk_context(event)
        required = _required_scanners(context, self.default_required_by_asset_kind)
        if not required:
            return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("SCANNER_COVERAGE_NOT_REQUIRED"))
        completed = _completed_scanner_tokens(context)
        missing = [scanner for scanner in required if scanner not in completed]
        if missing:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                confidence=0.85,
                reason=_reason(
                    "SCANNER_COVERAGE_MISSING",
                    scanner_coverage_gaps=[f"missing:{scanner}" for scanner in missing],
                    risk_hypotheses=["high-risk publication assets cannot be treated as safe until required scanner coverage is present"],
                    required_reviewers=["rights reviewer", "local/context reviewer"],
                    release_constraints=["attach completed scanner results or explicit review waiver before publication"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("SCANNER_COVERAGE_COMPLETE"))


class ScannerResultDetector(HarnessDetector):
    detector_id = "scanner_result_detector"

    blocking_severities = {"high", "critical"}

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        findings = _scanner_findings(_risk_context(event))
        risky = [
            finding
            for finding in findings
            if str(_lookup(finding, "severity") or "").lower() in self.blocking_severities
        ]
        if risky:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                confidence=max(float(_lookup(finding, "confidence") or 0.0) for finding in risky),
                reason=_reason(
                    "SCANNER_FINDINGS_REQUIRE_REVIEW",
                    scanner_findings=[_finding_summary(finding) for finding in risky],
                    similarity_matches=[_finding_summary(finding) for finding in risky if _finding_type(finding).startswith("similarity.")],
                    provenance_findings=[_finding_summary(finding) for finding in risky if _finding_type(finding).startswith("provenance.")],
                    risk_hypotheses=["external scanner surfaced structured asset risk that has not been counter-reviewed"],
                    required_reviewers=["local/context reviewer", "legal reviewer"],
                    release_constraints=["resolve or counter-approve high severity scanner findings before publication"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("NO_HIGH_SEVERITY_SCANNER_FINDINGS"))


class RollbackReadinessDetector(HarnessDetector):
    detector_id = "rollback_readiness_detector"

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        context = _risk_context(event)
        constraints = _lookup(context, "known_constraints") or {}
        review_route = _lookup(context, "review_route") or {}
        requires_rollback = bool(_lookup(constraints, "high_exposure")) or bool(_lookup(review_route, "requires_rollback"))
        if not requires_rollback:
            return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("ROLLBACK_NOT_REQUIRED"))
        rollback_plan = _lookup(context, "rollback_plan") or {}
        required = ["owner", "kill_switch", "fallback_asset"]
        missing = [field for field in required if _missing(_lookup(rollback_plan, field))]
        if missing:
            return DetectionResult(
                DetectionOutcome.DETECTED,
                confidence=0.8,
                reason=_reason(
                    "ROLLBACK_PLAN_INCOMPLETE",
                    rollback_constraints=missing,
                    risk_hypotheses=["high exposure publication lacks a pre-planned rollback path"],
                    required_reviewers=["release owner"],
                    release_constraints=["define rollback owner, kill switch, and fallback asset before publication"],
                ),
            )
        return DetectionResult(DetectionOutcome.CLEAN, reason=_reason("ROLLBACK_PLAN_READY"))


def _reason(code: str, **values: Any) -> dict[str, Any]:
    reason = {key: [] for key in AUDIT_REASON_KEYS}
    reason["code"] = code
    reason.update(values)
    return reason


def _risk_context(event: HarnessEvent) -> dict[str, Any]:
    data = to_plain(event)
    for path in (
        "risk.risk_context",
        "context.risk_context",
        "payload.risk_context",
        "payload.request.risk_context",
        "payload.request.args.risk_context",
    ):
        value = _lookup(data, path)
        if isinstance(value, dict):
            return value
    return {}


def _risk_evidence(event: HarnessEvent) -> dict[str, Any]:
    data = to_plain(event)
    for path in ("risk.evidence", "context.risk_evidence", "payload.risk_evidence", "payload.request.risk_evidence"):
        value = _lookup(data, path)
        if isinstance(value, dict):
            return value
    return {}


def _content(event: HarnessEvent) -> str:
    data = to_plain(event)
    parts: list[str] = []
    for path in ("payload.text", "payload.content", "payload.request.content", "payload.request.args.content", "payload.request.name"):
        value = _lookup(data, path)
        if value:
            parts.append(str(value))
    return " ".join(parts)


def _lookup(subject: Any, path: str | None) -> Any:
    if not path:
        return subject
    current = to_plain(subject) if is_dataclass(subject) else subject
    for part in path.split("."):
        if hasattr(current, part):
            current = getattr(current, part)
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _missing(value: Any) -> bool:
    return value in (None, "", [], {})


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "enabled", "approved"}
    return bool(value)


def _has_wordplay(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in ["!", " rhyme ", " pun ", "sounds like", "on the desk", "tap", "bang"])


def _scanner_findings(context: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for result in _lookup(context, "scanner_results") or []:
        scanner_id = _lookup(result, "scanner_id") or _lookup(result, "id")
        for finding in _lookup(result, "findings") or []:
            finding_dict = dict(finding) if isinstance(finding, dict) else to_plain(finding)
            if scanner_id and "source" not in finding_dict:
                finding_dict["source"] = scanner_id
            findings.append(finding_dict)
    return findings


def _required_scanners(context: dict[str, Any], defaults: dict[str, list[str]]) -> list[str]:
    coverage = _lookup(context, "scanner_coverage") or {}
    explicit = [_normalize_token(value) for value in _lookup(coverage, "required_scanners") or []]
    required = [value for value in explicit if value]
    asset_kind = _normalize_token(_lookup(context, "asset_kind"))
    if not required and asset_kind in defaults:
        required = list(defaults[asset_kind])
    rights = _lookup(context, "rights") or {}
    if _truthy(_lookup(rights, "uses_third_party_assets")):
        required.extend(["similarity", "provenance", "rights"])
    if _truthy(_lookup(rights, "uses_cultural_source")):
        required.extend(["provenance", "rights", "local_context"])
    waived = {_normalize_token(value) for value in _lookup(coverage, "waived_scanners") or []}
    return sorted({value for value in required if value and value not in waived})


def _completed_scanner_tokens(context: dict[str, Any]) -> set[str]:
    coverage = _lookup(context, "scanner_coverage") or {}
    completed = {_normalize_token(value) for value in _lookup(coverage, "completed_scanners") or []}
    for result in _lookup(context, "scanner_results") or []:
        status = str(_lookup(result, "status") or "completed").lower()
        if status not in {"completed", "passed", "clean"}:
            continue
        completed.update(_scanner_tokens(result))
    return {value for value in completed if value}


def _scanner_tokens(result: Any) -> set[str]:
    metadata = _lookup(result, "metadata") or {}
    values = [
        _lookup(result, "scanner_id"),
        _lookup(result, "id"),
        _lookup(metadata, "scanner_type"),
        _lookup(metadata, "type"),
    ]
    values.extend(_lookup(metadata, "capabilities") or [])
    tokens: set[str] = set()
    for value in values:
        token = _normalize_token(value)
        if token:
            tokens.add(token)
            tokens.update(part for part in token.split("_") if part)
    return tokens


def _normalize_token(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _finding_type(finding: dict[str, Any]) -> str:
    return str(_lookup(finding, "type") or "").lower()


def _finding_summary(finding: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": _lookup(finding, "type"),
        "severity": _lookup(finding, "severity"),
        "message": _lookup(finding, "message"),
        "source": _lookup(finding, "source"),
        "evidence_ref": _lookup(finding, "evidence_ref"),
        "confidence": _lookup(finding, "confidence"),
        "metadata": _finding_metadata_summary(_lookup(finding, "metadata") or {}),
    }


def _finding_metadata_summary(metadata: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "asset_region",
        "attribution",
        "license_status",
        "matched_asset_ref",
        "required_rights",
        "rights_status",
        "similarity_score",
        "source_ref",
        "source_type",
        "transform_type",
    ]
    return {key: metadata[key] for key in keys if key in metadata}
