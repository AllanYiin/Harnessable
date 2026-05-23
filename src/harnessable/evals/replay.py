from __future__ import annotations


class ReplayEngine:
    def __init__(self, kernel: object) -> None:
        self.kernel = kernel

    def replay(self, events: list[dict]) -> list[dict]:
        return [self.kernel.emit_from_dict(event).to_dict() for event in events]

    def diff(self, events: list[dict], baseline_decisions: list[dict]) -> dict:
        decisions = self.replay(events)
        return {"changed": decisions != baseline_decisions, "decisions": decisions, "baseline_decisions": baseline_decisions}
