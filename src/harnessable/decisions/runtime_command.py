from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuntimeCommandType(str, Enum):
    CONTINUE = "CONTINUE"
    MUTATE = "MUTATE"
    RETRY = "RETRY"
    ROUTE = "ROUTE"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    BLOCK = "BLOCK"
    ABORT = "ABORT"
    ROLLBACK = "ROLLBACK"
    FAIL_SAFE = "FAIL_SAFE"


@dataclass(slots=True)
class RuntimeCommand:
    command_type: RuntimeCommandType
    reason: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
