from __future__ import annotations

import time
from dataclasses import dataclass

from harnessable.capabilities.health import CapabilityHealth


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 3
    cooldown_seconds: float = 1.0
    failures: int = 0
    opened_at: float | None = None
    state: CapabilityHealth = CapabilityHealth.HEALTHY

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None
        self.state = CapabilityHealth.HEALTHY

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = CapabilityHealth.OPEN_CIRCUIT
            self.opened_at = time.time()

    def allow_request(self) -> bool:
        if self.state != CapabilityHealth.OPEN_CIRCUIT:
            return True
        if self.opened_at is not None and time.time() - self.opened_at >= self.cooldown_seconds:
            self.state = CapabilityHealth.HALF_OPEN
            return True
        return False
