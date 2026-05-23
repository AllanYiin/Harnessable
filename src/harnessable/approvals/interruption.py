from __future__ import annotations

from dataclasses import dataclass

from harnessable.state import RunCheckpoint


@dataclass(slots=True)
class RunInterruption:
    approval_id: str
    checkpoint: RunCheckpoint
    status: str = "INTERRUPTED"


class InterruptionStore:
    def __init__(self) -> None:
        self.interruptions: dict[str, RunInterruption] = {}

    def save(self, interruption: RunInterruption) -> None:
        self.interruptions[interruption.approval_id] = interruption

    def get(self, approval_id: str) -> RunInterruption:
        return self.interruptions[approval_id]
