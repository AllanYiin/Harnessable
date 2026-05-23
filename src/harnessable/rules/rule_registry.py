from __future__ import annotations

from harnessable.core.errors import NotFoundError
from harnessable.events import HarnessEvent

from .schemas import HarnessRule


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: dict[str, HarnessRule] = {}

    def add(self, rule: HarnessRule) -> None:
        self._rules[rule.id] = rule

    create = add

    def get(self, rule_id: str) -> HarnessRule:
        try:
            return self._rules[rule_id]
        except KeyError as exc:
            raise NotFoundError(f"rule not found: {rule_id}") from exc

    def list(self) -> list[HarnessRule]:
        return list(self._rules.values())

    def update(self, rule: HarnessRule) -> None:
        self.get(rule.id)
        self._rules[rule.id] = rule

    def enable(self, rule_id: str) -> None:
        self.get(rule_id).enabled = True

    def disable(self, rule_id: str) -> None:
        self.get(rule_id).enabled = False

    def shadow(self, rule_id: str, enabled: bool = True) -> None:
        self.get(rule_id).shadow = enabled

    def archive(self, rule_id: str) -> None:
        rule = self.get(rule_id)
        rule.enabled = False
        rule.archived = True

    def match(self, event: HarnessEvent) -> list[HarnessRule]:
        return [rule for rule in self._rules.values() if self._matches(rule, event)]

    def _matches(self, rule: HarnessRule, event: HarnessEvent) -> bool:
        if not rule.enabled or rule.archived:
            return False
        applies = rule.applies_to or {}
        if not _wildcard_match(applies.get("event_types"), event.event_type.value):
            return False
        if not _wildcard_match(applies.get("runtimes"), event.runtime_type):
            return False
        if not _wildcard_match(applies.get("capability_types"), event.capability_type):
            return False
        if not _wildcard_match(applies.get("actors"), event.actor_role or event.actor.get("id")):
            return False
        hook = rule.hook or {}
        if hook.get("point") and event.hook_point and hook["point"] != event.hook_point:
            return False
        return True


def _wildcard_match(patterns: object, value: str | None) -> bool:
    if patterns in (None, [], "*"):
        return True
    if isinstance(patterns, str):
        patterns = [patterns]
    if not isinstance(patterns, list):
        return True
    return "*" in patterns or value in patterns
