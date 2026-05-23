from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GatewayContext:
    run_id: str
    actor_role: str = "assistant"
    runtime_type: str = "agent"
    metadata: dict[str, Any] = field(default_factory=dict)
