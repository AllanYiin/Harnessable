from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RunCheckpoint:
    run_id: str
    event_id: str
    state: dict[str, Any] = field(default_factory=dict)
