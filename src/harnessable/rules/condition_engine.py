from __future__ import annotations

from typing import Any


class ConditionEngine:
    def evaluate(self, condition: dict[str, Any] | None, subject: Any) -> bool:
        if not condition:
            return True
        if "all_of" in condition:
            return all(self.evaluate(c, subject) for c in condition["all_of"])
        if "any_of" in condition:
            return any(self.evaluate(c, subject) for c in condition["any_of"])
        if "not" in condition:
            return not self.evaluate(condition["not"], subject)
        field = condition.get("field")
        value = self._lookup(subject, field) if field else None
        if "equals" in condition:
            return value == condition["equals"]
        if "in" in condition:
            return value in condition["in"]
        if "contains" in condition:
            return condition["contains"] in (value or "")
        if "exists" in condition:
            return (value is not None) is bool(condition["exists"])
        return True

    def _lookup(self, subject: Any, path: str | None) -> Any:
        if not path:
            return subject
        current = subject
        for part in path.split("."):
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
