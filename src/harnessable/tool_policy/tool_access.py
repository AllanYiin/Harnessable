from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TOOL_ACCESS_POLICY_VERSION = 1


@dataclass(frozen=True)
class ToolCapabilityProfile:
    name: str
    capability_class: str = "tool"
    requires_tool_policy: bool = False
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = TOOL_ACCESS_POLICY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "capability_class": self.capability_class,
            "requires_tool_policy": self.requires_tool_policy,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCapabilityProfile":
        return cls(
            schema_version=int(data.get("schema_version") or TOOL_ACCESS_POLICY_VERSION),
            name=str(data.get("name") or ""),
            capability_class=str(data.get("capability_class") or "tool"),
            requires_tool_policy=bool(data.get("requires_tool_policy", False)),
            enabled=bool(data.get("enabled", True)),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True)
class ToolExposureDecision:
    enabled_tool_names: list[str]
    excluded_tool_names: list[str]
    denied_reasons: dict[str, str] = field(default_factory=dict)
    schema_version: int = TOOL_ACCESS_POLICY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "enabled_tool_names": list(self.enabled_tool_names),
            "excluded_tool_names": list(self.excluded_tool_names),
            "denied_reasons": dict(self.denied_reasons),
        }


def build_tool_exposure_decision(
    *,
    tool_names: tuple[str, ...] | list[str],
    tool_policy_enabled: bool,
    globally_excluded_tool_names: tuple[str, ...] | list[str] = (),
    profiles: tuple[ToolCapabilityProfile, ...] | list[ToolCapabilityProfile] = (),
) -> ToolExposureDecision:
    excluded = set(str(name) for name in globally_excluded_tool_names)
    profile_by_name = {profile.name: profile for profile in profiles}
    denied_reasons: dict[str, str] = {}
    enabled_tool_names: list[str] = []
    excluded_tool_names: list[str] = []

    for tool_name in dict.fromkeys(str(name) for name in tool_names):
        profile = profile_by_name.get(tool_name)
        reason = ""
        if tool_name in excluded:
            reason = "globally_excluded"
        elif profile is not None and not profile.enabled:
            reason = "capability_disabled"
        elif profile is not None and profile.requires_tool_policy and not tool_policy_enabled:
            reason = "tool_policy_required"

        if reason:
            excluded_tool_names.append(tool_name)
            denied_reasons[tool_name] = reason
        else:
            enabled_tool_names.append(tool_name)

    return ToolExposureDecision(
        enabled_tool_names=enabled_tool_names,
        excluded_tool_names=excluded_tool_names,
        denied_reasons=denied_reasons,
    )
