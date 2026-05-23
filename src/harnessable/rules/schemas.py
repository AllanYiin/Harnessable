from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from harnessable.core.errors import ValidationError
from harnessable.core.serialization import to_plain
from harnessable.decisions import DecisionEffect


class RuleMode(str, Enum):
    BLOCKING = "blocking"
    OBSERVE = "observe"
    SHADOW = "shadow"


@dataclass(slots=True)
class HarnessRule:
    id: str
    name: str
    version: str = "1.0.0"
    enabled: bool = True
    shadow: bool = False
    applies_to: dict[str, Any] = field(default_factory=dict)
    hook: dict[str, Any] = field(default_factory=dict)
    condition: dict[str, Any] | None = None
    detector: dict[str, Any] = field(default_factory=lambda: {"type": "always_allow"})
    action: dict[str, Any] = field(default_factory=lambda: {"when_detected": {"type": "ALLOW"}})
    severity: str = "info"
    telemetry: dict[str, Any] = field(default_factory=dict)
    testing: dict[str, Any] = field(default_factory=dict)
    ownership: dict[str, Any] = field(default_factory=dict)
    archived: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("rule id is required")
        if not self.name:
            raise ValidationError("rule name is required")

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessRule":
        return cls(**dict(data))

    def effect_for(self, outcome: str) -> DecisionEffect:
        key = {
            "detected": "when_detected",
            "clean": "when_clean",
            "uncertain": "when_uncertain",
            "failed": "when_detector_failed",
        }.get(outcome, "when_detected")
        action = self.action.get(key) or self.action.get("when_detected") or {"type": "ALLOW"}
        return DecisionEffect(action.get("type", "ALLOW"))
