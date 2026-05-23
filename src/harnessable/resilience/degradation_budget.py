from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DegradationBudget:
    max_total_attempts: int = 3
    max_fallback_depth: int = 2
    max_added_latency_ms: int = 10_000
    max_added_cost_usd: float = 0.0
    attempts: int = 0
    depth: int = 0
    added_latency_ms: int = 0
    added_cost_usd: float = 0.0

    def exhausted(self) -> bool:
        return (
            self.attempts >= self.max_total_attempts
            or self.depth >= self.max_fallback_depth
            or self.added_latency_ms > self.max_added_latency_ms
            or self.added_cost_usd > self.max_added_cost_usd
        )
