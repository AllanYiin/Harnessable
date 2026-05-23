from __future__ import annotations

from harnessable.core.errors import NotFoundError

from .schemas import CapabilityProfile


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityProfile] = {}

    def add(self, capability: CapabilityProfile) -> None:
        self._capabilities[capability.id] = capability

    create = add

    def get(self, capability_id: str) -> CapabilityProfile:
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise NotFoundError(f"capability not found: {capability_id}") from exc

    def list(self) -> list[CapabilityProfile]:
        return list(self._capabilities.values())

    def update(self, capability: CapabilityProfile) -> None:
        self.get(capability.id)
        self._capabilities[capability.id] = capability

    def archive(self, capability_id: str) -> None:
        cap = self.get(capability_id)
        cap.enabled = False
        cap.archived = True
