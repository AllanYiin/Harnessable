from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harnessable.identity import Principal

from .schemas import CapabilityProfile


@dataclass(frozen=True)
class PermissionContext:
    role: str | None = None
    tenant_id: str | None = None
    purpose: str | None = None
    principal_id: str | None = None
    project_id: str | None = None
    project_memberships: tuple[str, ...] = ()
    approval_authorities: tuple[str, ...] = ()

    @classmethod
    def from_principal(
        cls,
        principal: Principal,
        *,
        purpose: str | None = None,
        project_id: str | None = None,
    ) -> "PermissionContext":
        return cls(
            role=principal.role,
            tenant_id=principal.tenant_id,
            purpose=purpose,
            principal_id=principal.principal_id,
            project_id=project_id,
            project_memberships=principal.project_memberships,
            approval_authorities=principal.approval_authorities,
        )


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
        project_id: str | None = None,
        project_memberships: tuple[str, ...] = (),
        approval_authorities: tuple[str, ...] = (),
    ) -> bool:
        return self.decision(
            capability,
            PermissionContext(
                role=role,
                tenant_id=tenant_id,
                purpose=purpose,
                project_id=project_id,
                project_memberships=project_memberships,
                approval_authorities=approval_authorities,
            ),
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
        allowed_purposes = permissions.get("allowed_purposes") or []
        denied_purposes = permissions.get("denied_purposes") or []
        allowed_project_ids = permissions.get("allowed_project_ids") or permissions.get("required_project_ids") or []
        required_authorities = permissions.get("required_approval_authorities") or []
        if context.role in denied_roles:
            return PermissionDecision(False, "role_denied")
        if context.tenant_id and context.tenant_id in denied_tenants:
            return PermissionDecision(False, "tenant_denied")
        if allowed_tenants and context.tenant_id not in allowed_tenants:
            return PermissionDecision(False, "tenant_not_allowed")
        if context.purpose and context.purpose in denied_purposes:
            return PermissionDecision(False, "purpose_denied")
        if allowed_purposes and context.purpose not in allowed_purposes:
            return PermissionDecision(False, "purpose_not_allowed")
        if allowed_project_ids:
            memberships = set(context.project_memberships)
            if context.project_id:
                memberships.add(context.project_id)
            if not memberships.intersection(set(allowed_project_ids)):
                return PermissionDecision(False, "project_membership_required")
        if required_authorities and not set(required_authorities).issubset(set(context.approval_authorities)):
            return PermissionDecision(False, "approval_authority_missing")
        if not allowed_roles:
            return PermissionDecision(False, "no_allowed_roles")
        if context.role in allowed_roles or "*" in allowed_roles:
            return PermissionDecision(True, "allowed")
        return PermissionDecision(False, "role_not_allowed")
