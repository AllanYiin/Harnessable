from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DetectionOutcome(str, Enum):
    DETECTED = "detected"
    CLEAN = "clean"
    UNCERTAIN = "uncertain"
    FAILED = "failed"


@dataclass(slots=True)
class DetectionResult:
    outcome: DetectionOutcome
    confidence: float = 1.0
    reason: dict[str, Any] = field(default_factory=dict)
