from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TraceRecord:
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)


class TraceRecorder:
    def __init__(self, metadata_only: bool = True) -> None:
        self.metadata_only = metadata_only
        self.records: list[TraceRecord] = []

    def record(self, kind: str, payload: dict[str, Any]) -> None:
        if self.metadata_only:
            payload = {k: v for k, v in payload.items() if k not in {"payload", "content", "secret", "token"}}
        self.records.append(TraceRecord(kind, payload))

    def by_kind(self, kind: str) -> list[TraceRecord]:
        return [record for record in self.records if record.kind == kind]
