from __future__ import annotations

import re
from typing import Any

from harnessable.events import HarnessEvent
from .base import HarnessDetector, StreamingDetector
from .results import DetectionOutcome, DetectionResult


class AlwaysAllowDetector(HarnessDetector):
    detector_id = "always_allow"

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        return DetectionResult(DetectionOutcome.CLEAN)


class RegexDetector(HarnessDetector):
    detector_id = "regex"

    def __init__(self, field: str, pattern: str, flags: int = re.IGNORECASE) -> None:
        self.field = field
        self.pattern = re.compile(pattern, flags)

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        value = _lookup(event, self.field)
        matched = bool(self.pattern.search(str(value or "")))
        return DetectionResult(
            DetectionOutcome.DETECTED if matched else DetectionOutcome.CLEAN,
            confidence=1.0,
            reason={"code": "REGEX_MATCH" if matched else "REGEX_NO_MATCH", "field": self.field},
        )


class RequiredFieldDetector(HarnessDetector):
    detector_id = "required_field"

    def __init__(self, field: str) -> None:
        self.field = field

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        value = _lookup(event, self.field)
        missing = value in (None, "")
        return DetectionResult(
            DetectionOutcome.DETECTED if missing else DetectionOutcome.CLEAN,
            reason={"code": "REQUIRED_FIELD_MISSING" if missing else "REQUIRED_FIELD_PRESENT", "field": self.field},
        )


class FakeStreamingInferentialDetector(StreamingDetector):
    detector_id = "fake_inferential"

    def __init__(self, outcome: DetectionOutcome = DetectionOutcome.UNCERTAIN) -> None:
        self.outcome = outcome

    def evaluate(self, event: HarnessEvent, state: object | None = None, artifacts: object | None = None) -> DetectionResult:
        return DetectionResult(self.outcome, confidence=0.5, reason={"code": "FAKE_STREAMING_DETECTOR"})

    async def evaluate_stream(self, event: HarnessEvent):
        for chunk in ["evaluating", ":", self.outcome.value]:
            yield chunk


def detector_from_config(config: dict[str, Any]) -> HarnessDetector:
    kind = config.get("type") or config.get("implementation") or "always_allow"
    if kind in {"always_allow", "computational"}:
        return AlwaysAllowDetector()
    if kind == "regex":
        return RegexDetector(config["field"], config["pattern"])
    if kind == "required_field":
        return RequiredFieldDetector(config["field"])
    if kind in {"inferential", "fake_inferential"}:
        return FakeStreamingInferentialDetector()
    return AlwaysAllowDetector()


def _lookup(subject: Any, path: str | None) -> Any:
    if not path:
        return subject
    current = subject
    for part in path.split("."):
        if hasattr(current, part):
            current = getattr(current, part)
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
