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


def _has_wordplay(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in ["!", " rhyme ", " pun ", "sounds like", "on the desk", "tap", "bang"])
