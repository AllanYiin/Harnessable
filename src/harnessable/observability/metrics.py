from __future__ import annotations

from collections import Counter


class MetricsCollector:
    def __init__(self) -> None:
        self.counters: Counter[str] = Counter()

    def increment(self, name: str, count: int = 1) -> None:
        self.counters[name] += count

    def snapshot(self) -> dict[str, int]:
        return dict(self.counters)
