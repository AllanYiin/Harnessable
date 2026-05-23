from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SideEffectState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    STARTED = "STARTED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(slots=True)
class SideEffectRecord:
    operation_id: str
    state: SideEffectState = SideEffectState.NOT_STARTED


class SideEffectTracker:
    def __init__(self) -> None:
        self.records: dict[str, SideEffectRecord] = {}

    def set_state(self, operation_id: str, state: SideEffectState) -> SideEffectRecord:
        record = self.records.get(operation_id, SideEffectRecord(operation_id))
        record.state = state
        self.records[operation_id] = record
        return record

    def can_retry(self, operation_id: str) -> bool:
        record = self.records.get(operation_id)
        return record is None or record.state in {SideEffectState.NOT_STARTED, SideEffectState.FAILED}
