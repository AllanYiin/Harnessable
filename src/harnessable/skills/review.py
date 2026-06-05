from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from jsonschema import validate

from .schemas import SkillCandidate, SkillManifest
from .selector import SkillSelector


SKILL_ROUTING_REVIEW_TOOL_NAME = "skill_routing_review"

SKILL_ROUTING_REVIEW_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["decision", "selected_skill_ids", "confidence", "reasons", "should_hydrate"],
    "properties": {
        "decision": {"type": "string", "enum": ["none", "keep", "add", "replace"]},
        "selected_skill_ids": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasons": {"type": "array", "items": {"type": "string"}},
        "should_hydrate": {"type": "boolean"},
    },
}


@dataclass(slots=True)
class SkillRoutingReviewRequest:
    task_text: str
    trigger: str
    selected_skill_ids: list[str] = field(default_factory=list)
    candidates: list[SkillCandidate] = field(default_factory=list)
    available_manifests: list[SkillManifest] = field(default_factory=list)
    audit_reasons: list[str] = field(default_factory=list)

    def to_tool_input(self) -> dict[str, Any]:
        return {
            "task_text": self.task_text,
            "trigger": self.trigger,
            "selected_skill_ids": list(self.selected_skill_ids),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "available_manifests": [manifest.to_prompt_metadata() for manifest in self.available_manifests],
            "audit_reasons": list(self.audit_reasons),
        }


@dataclass(slots=True)
class SkillRoutingReviewResult:
    decision: str
    selected_skill_ids: list[str]
    confidence: float
    reasons: list[str]
    should_hydrate: bool

    def __post_init__(self) -> None:
        validate(self.to_dict(), SKILL_ROUTING_REVIEW_JSON_SCHEMA)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "selected_skill_ids": list(self.selected_skill_ids),
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "should_hydrate": self.should_hydrate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillRoutingReviewResult":
        validate(data, SKILL_ROUTING_REVIEW_JSON_SCHEMA)
        return cls(
            decision=str(data["decision"]),
            selected_skill_ids=[str(item) for item in data["selected_skill_ids"]],
            confidence=float(data["confidence"]),
            reasons=[str(item) for item in data["reasons"]],
            should_hydrate=bool(data["should_hydrate"]),
        )


class SkillRoutingReviewTool(Protocol):
    name: str

    def review(self, request: SkillRoutingReviewRequest) -> SkillRoutingReviewResult | dict[str, Any]: ...


class DeterministicSkillRoutingReviewTool:
    name = SKILL_ROUTING_REVIEW_TOOL_NAME

    def __init__(self, selector: SkillSelector | None = None, confidence_threshold: float = 0.55) -> None:
        self.selector = selector or SkillSelector()
        self.confidence_threshold = confidence_threshold

    def review(self, request: SkillRoutingReviewRequest) -> SkillRoutingReviewResult:
        selected = list(request.selected_skill_ids)
        reasons = [f"trigger:{request.trigger}"]
        if request.trigger == "close_score" and request.candidates:
            top = request.candidates[:2]
            selected = [candidate.manifest.id for candidate in top]
            confidence = min(0.85, max(0.55, top[0].score / max(1.0, sum(candidate.score for candidate in top))))
            return SkillRoutingReviewResult(
                decision="add" if selected else "none",
                selected_skill_ids=selected,
                confidence=confidence,
                reasons=reasons + ["close candidate scores require joint hydration"],
                should_hydrate=bool(selected),
            )

        candidates = [
            SkillCandidate(manifest=manifest, score=score, reasons=reason_list)
            for manifest in request.available_manifests
            for score, reason_list, explicit in [self.selector._score(request.task_text, manifest, set())]
            if score > 0 and not explicit
        ]
        candidates.sort(key=lambda item: (-item.score, item.manifest.priority, item.manifest.id))
        if candidates:
            selected = [candidate.manifest.id for candidate in candidates[:4]]
            confidence = 0.7
            decision = "add"
        else:
            confidence = 0.2
            decision = "none"
        return SkillRoutingReviewResult(
            decision=decision,
            selected_skill_ids=selected,
            confidence=confidence,
            reasons=reasons + list(request.audit_reasons),
            should_hydrate=bool(selected) and confidence >= self.confidence_threshold,
        )


def normalize_review_result(result: SkillRoutingReviewResult | dict[str, Any]) -> SkillRoutingReviewResult:
    if isinstance(result, SkillRoutingReviewResult):
        return result
    return SkillRoutingReviewResult.from_dict(result)
