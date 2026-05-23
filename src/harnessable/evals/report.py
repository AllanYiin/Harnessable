from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ReplayReport:
    run_id: str
    decisions: list[dict]
    baseline_decisions: list[dict] | None = None

    @property
    def changed(self) -> bool:
        return self.baseline_decisions is not None and self.baseline_decisions != self.decisions

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "decisions": self.decisions,
            "baseline_decisions": self.baseline_decisions,
            "changed": self.changed,
        }
