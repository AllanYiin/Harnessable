from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harnessable.core.errors import ValidationError
from harnessable.core.serialization import to_plain


@dataclass(slots=True)
class FallbackPolicy:
    id: str
    name: str
    schema_version: str = "1"
    enabled: bool = True
    version: str = "1.0.0"
    applies_to: dict[str, Any] = field(default_factory=dict)
    triggers: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    fallback_graph: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("fallback policy id is required")
        if not self.constraints:
            raise ValidationError("fallback policy constraints are required")

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FallbackPolicy":
        return cls(**dict(data))
