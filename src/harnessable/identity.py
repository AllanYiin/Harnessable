from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Principal:
    principal_id: str
    role: str
    tenant_id: str | None = None
    project_memberships: tuple[str, ...] = field(default_factory=tuple)
    approval_authorities: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_memberships", tuple(self.project_memberships))
        object.__setattr__(self, "approval_authorities", tuple(self.approval_authorities))

    def to_dict(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "role": self.role,
            "tenant_id": self.tenant_id,
            "project_memberships": list(self.project_memberships),
            "approval_authorities": list(self.approval_authorities),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Principal":
        return cls(
            principal_id=str(payload["principal_id"]),
            role=str(payload["role"]),
            tenant_id=payload.get("tenant_id"),
            project_memberships=tuple(payload.get("project_memberships") or ()),
            approval_authorities=tuple(payload.get("approval_authorities") or ()),
        )
