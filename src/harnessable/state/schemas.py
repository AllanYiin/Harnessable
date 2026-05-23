from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from harnessable.core.serialization import parse_enum, to_plain


class ProjectStatus(str, Enum):
    NEW = "NEW"
    OPEN = "OPEN"
    DIRTY = "DIRTY"
    SAVED = "SAVED"
    ARCHIVED = "ARCHIVED"


@dataclass(slots=True)
class ProjectManifest:
    name: str
    profile: str = "default"
    version: str = "0.1.0"
    status: ProjectStatus = ProjectStatus.NEW
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.status = parse_enum(ProjectStatus, self.status)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectManifest":
        data = dict(data)
        data["status"] = parse_enum(ProjectStatus, data.get("status", ProjectStatus.NEW))
        return cls(**data)


@dataclass(slots=True)
class RunState:
    run_id: str
    status: str = "RUNNING"
    checkpoint_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return to_plain(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunState":
        return cls(**dict(data))
