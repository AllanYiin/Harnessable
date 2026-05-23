from __future__ import annotations

from .schemas import CapabilityProfile


class PermissionChecker:
    def allowed(self, capability: CapabilityProfile, role: str | None) -> bool:
        permissions = capability.permissions or {}
        allowed_roles = permissions.get("allowed_roles") or []
        denied_roles = permissions.get("denied_roles") or []
        if role in denied_roles:
            return False
        if not allowed_roles:
            return False
        return role in allowed_roles or "*" in allowed_roles
