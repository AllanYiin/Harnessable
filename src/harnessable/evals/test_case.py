from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EvalCase:
    id: str
    event: dict[str, Any]
    expected_effect: str
    metadata: dict[str, Any] = field(default_factory=dict)
