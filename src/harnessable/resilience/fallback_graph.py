from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FallbackStep:
    id: str
    action_type: str
    level: str = "L1_LOCAL_RECOVERY"
    target: str | None = None
    selector: dict[str, Any] | None = None
    disclosure: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None


class FallbackGraphPlanner:
    def plan(self, graph: list[dict[str, Any]]) -> list[FallbackStep]:
        steps: list[FallbackStep] = []
        for node in graph:
            action = node.get("action") or {}
            steps.append(
                FallbackStep(
                    id=node["id"],
                    level=node.get("level", "L1_LOCAL_RECOVERY"),
                    action_type=action.get("type", "FAIL_SAFE"),
                    target=action.get("target"),
                    selector=action.get("selector"),
                    disclosure=node.get("disclosure"),
                    raw=node,
                )
            )
        return steps
