from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from harnessable.core.serialization import parse_enum, to_plain

from .effects import DecisionEffect


@dataclass(slots=True)
class HarnessDecision:
    event_id: str
    schema_version: str = "1"
    effect: DecisionEffect = DecisionEffect.ALLOW
    decision_id: str = field(default_factory=lambda: f"decision_{uuid4().hex}")
    rule_id: str | None = None
    severity: str = "info"
    confidence: float = 1.0
    reason: dict[str, Any] = field(default_factory=dict)
    mutation: dict[str, Any] | None = None
    approval: dict[str, Any] = field(default_factory=dict)
    retry: dict[str, Any] = field(default_factory=dict)
    route: dict[str, Any] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    shadow: bool = False
    contributing_decisions: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.effect = parse_enum(DecisionEffect, self.effect)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessDecision":
        data = dict(data)
        data["effect"] = parse_enum(DecisionEffect, data["effect"])
        return cls(**data)

    @classmethod
    def allow(cls, event_id: str) -> "HarnessDecision":
        return cls(event_id=event_id, effect=DecisionEffect.ALLOW)
