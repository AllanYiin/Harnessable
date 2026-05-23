from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from harnessable.core.serialization import parse_enum, to_plain


class FailureLayer(str, Enum):
    MODEL = "MODEL"
    TOOL = "TOOL"
    MEMORY = "MEMORY"
    RESOURCE = "RESOURCE"
    AGENT = "AGENT"
    EXTERNAL_ACTION = "EXTERNAL_ACTION"
    RUNTIME = "RUNTIME"


class FailureCategory(str, Enum):
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    PROVIDER_5XX = "PROVIDER_5XX"
    VALIDATION = "VALIDATION"
    PERMISSION = "PERMISSION"
    SIDE_EFFECT_UNKNOWN = "SIDE_EFFECT_UNKNOWN"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class FailureSignal:
    run_id: str
    event_id: str
    layer: FailureLayer
    category: FailureCategory
    id: str = field(default_factory=lambda: f"fail_{uuid4().hex}")
    recoverability: str = "TRANSIENT"
    severity: str = "MEDIUM"
    retryable: bool = True
    fallback_allowed: bool = True
    source: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    risk: dict[str, Any] = field(default_factory=dict)
    suggested_actions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.layer = parse_enum(FailureLayer, self.layer)
        self.category = parse_enum(FailureCategory, self.category)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FailureSignal":
        data = dict(data)
        data["layer"] = parse_enum(FailureLayer, data["layer"])
        data["category"] = parse_enum(FailureCategory, data["category"])
        return cls(**data)
