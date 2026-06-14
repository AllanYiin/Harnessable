from __future__ import annotations

from .schemas import CapabilityProfile, CapabilityType


class CapabilitySelector:
    def select(
        self,
        capabilities: list[CapabilityProfile],
        capability_type: CapabilityType | str | None = None,
        compatibility_class: str | None = None,
        required_features: list[str] | None = None,
        side_effect: bool | None = None,
        source: CapabilityProfile | None = None,
    ) -> list[CapabilityProfile]:
        required_features = required_features or []
        results: list[CapabilityProfile] = []
        for cap in capabilities:
            if not cap.enabled or cap.archived:
                continue
            expected_type = capability_type.value if isinstance(capability_type, CapabilityType) else capability_type
            if expected_type and cap.type.value != expected_type:
                continue
            if compatibility_class and cap.compatibility_class != compatibility_class:
                continue
            if side_effect is not None and bool(cap.risk.get("side_effect")) is not side_effect:
                continue
            if not set(required_features).issubset(set(cap.supports)):
                continue
            if source and self._is_wider_than_source(cap, source):
                continue
            results.append(cap)
        return results

    def _is_wider_than_source(self, candidate: CapabilityProfile, source: CapabilityProfile) -> bool:
        source_allowed = set(source.permissions.get("allowed_roles") or [])
        candidate_allowed = set(candidate.permissions.get("allowed_roles") or [])
        if "*" in candidate_allowed and "*" not in source_allowed:
            return True
        if source_allowed and not candidate_allowed.issubset(source_allowed | {"*"}):
            return True
        for key in ("allowed_tenant_ids", "allowed_purposes", "allowed_project_ids", "required_project_ids"):
            source_values = set(source.permissions.get(key) or [])
            candidate_values = set(candidate.permissions.get(key) or [])
            if source_values and not candidate_values.issubset(source_values):
                return True
            if not source_values and candidate_values:
                return True
        source_authorities = set(source.permissions.get("required_approval_authorities") or [])
        candidate_authorities = set(candidate.permissions.get("required_approval_authorities") or [])
        return bool(source_authorities and not candidate_authorities.issuperset(source_authorities))
