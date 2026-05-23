from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from harnessable.core.errors import ValidationError
from harnessable.core.serialization import parse_enum, to_plain


class CapabilityType(str, Enum):
    MODEL = "MODEL"
    TOOL = "TOOL"
    MEMORY = "MEMORY"
    RESOURCE = "RESOURCE"
    AGENT = "AGENT"
    EXTERNAL_ACTION = "EXTERNAL_ACTION"


@dataclass(slots=True)
class CapabilityProfile:
    id: str
    type: CapabilityType
    schema_version: str = "1"
    name: str | None = None
    owner: str | None = None
    compatibility_class: str | None = None
    contracts: dict[str, Any] = field(default_factory=dict)
    supports: list[str] = field(default_factory=list)
    risk: dict[str, Any] = field(default_factory=dict)
    permissions: dict[str, Any] = field(default_factory=dict)
    approval: dict[str, Any] = field(default_factory=dict)
    fallback: dict[str, Any] = field(default_factory=dict)
    observability: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    archived: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("capability id is required")
        self.type = parse_enum(CapabilityType, self.type)
        if self.type == CapabilityType.EXTERNAL_ACTION and "side_effect" not in self.risk:
            raise ValidationError("external action capability must declare side_effect")

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityProfile":
        data = dict(data)
        data["type"] = parse_enum(CapabilityType, data["type"])
        return cls(**data)
