from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schemas import CapabilityProfile


@dataclass(frozen=True)
class PermissionContext:
    role: str | None = None
    tenant_id: str | None = None
    purpose: str | None = None


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "reason": self.reason}


class PermissionChecker:
    def allowed(
        self,
        capability: CapabilityProfile,
        role: str | None,
        *,
        tenant_id: str | None = None,
        purpose: str | None = None,
    ) -> bool:
        return self.decision(
            capability,
            PermissionContext(role=role, tenant_id=tenant_id, purpose=purpose),
        ).allowed

    def decision(
        self,
        capability: CapabilityProfile,
        context: PermissionContext,
    ) -> PermissionDecision:
        permissions = capability.permissions or {}
        allowed_roles = permissions.get("allowed_roles") or []
        denied_roles = permissions.get("denied_roles") or []
        allowed_tenants = permissions.get("allowed_tenant_ids") or []
        denied_tenants = permissions.get("denied_tenant_ids") or []
        if context.role in denied_roles:
            return PermissionDecision(False, "role_denied")
        if context.tenant_id and context.tenant_id in denied_tenants:
            return PermissionDecision(False, "tenant_denied")
        if allowed_tenants and context.tenant_id not in allowed_tenants:
            return PermissionDecision(False, "tenant_not_allowed")
        if not allowed_roles:
            return PermissionDecision(False, "no_allowed_roles")
        if context.role in allowed_roles or "*" in allowed_roles:
            return PermissionDecision(True, "allowed")
        return PermissionDecision(False, "role_not_allowed")
