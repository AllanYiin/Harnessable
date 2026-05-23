from __future__ import annotations

from harnessable.events import HarnessEvent

from .failure_signal import FailureSignal
from .fallback_policy_schema import FallbackPolicy


class FallbackPolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[str, FallbackPolicy] = {}

    def add(self, policy: FallbackPolicy) -> None:
        self._policies[policy.id] = policy

    def match(self, event: HarnessEvent, signal: FailureSignal) -> list[FallbackPolicy]:
        results = []
        for policy in self._policies.values():
            if not policy.enabled:
                continue
            applies = policy.applies_to or {}
            event_types = applies.get("event_types") or ["*"]
            capability_types = applies.get("capability_types") or ["*"]
            if "*" not in event_types and event.event_type.value not in event_types:
                continue
            if "*" not in capability_types and event.capability_type not in capability_types:
                continue
            results.append(policy)
        return results
