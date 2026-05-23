from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OPEN_CIRCUIT = "OPEN_CIRCUIT"
    HALF_OPEN = "HALF_OPEN"
    DISABLED = "DISABLED"


@dataclass(slots=True)
class HealthSnapshot:
    status: CapabilityHealth = CapabilityHealth.HEALTHY
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    p95_latency_ms: int = 0


class CapabilityHealthMonitor:
    def __init__(self) -> None:
        self._snapshots: dict[str, HealthSnapshot] = {}

    def set(self, capability_id: str, snapshot: HealthSnapshot) -> None:
        self._snapshots[capability_id] = snapshot

    def get(self, capability_id: str) -> HealthSnapshot:
        return self._snapshots.get(capability_id, HealthSnapshot())
