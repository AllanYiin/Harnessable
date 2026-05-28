from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harnessable.core.serialization import to_plain


@dataclass(slots=True)
class RiskContext:
    jurisdiction: str | None = None
    locale: str | None = None
    release_at: str | None = None
    audience: str | list[str] | None = None
    channel: str | None = None
    intent: str | None = None
    artifact_refs: list[str] = field(default_factory=list)
    ai_generated: bool | None = None
    known_constraints: dict[str, Any] = field(default_factory=dict)
    review_route: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskContext":
        return cls(**dict(data))
