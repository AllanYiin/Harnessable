from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from harnessable.core.errors import ValidationError
from harnessable.core.serialization import parse_enum, to_plain

from .types import EventType


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class HarnessEvent:
    event_id: str
    run_id: str
    event_type: EventType
    runtime_type: str = "chat"
    hook_point: str | None = None
    phase: str | None = None
    trace_id: str | None = None
    parent_event_id: str | None = None
    timestamp: str = field(default_factory=_now_iso)
    actor: dict[str, Any] = field(default_factory=dict)
    capability: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    risk: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValidationError("event_id is required")
        if not self.run_id:
            raise ValidationError("run_id is required")
        self.event_type = parse_enum(EventType, self.event_type)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessEvent":
        data = dict(data)
        data["event_type"] = parse_enum(EventType, data["event_type"])
        return cls(**data)

    @property
    def capability_type(self) -> str | None:
        value = self.capability.get("type")
        return value.value if hasattr(value, "value") else value

    @property
    def actor_role(self) -> str | None:
        return self.actor.get("role")
